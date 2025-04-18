import numpy as np
from qiskit import QuantumCircuit,transpile
from qiskit.qasm2 import dumps
from ....utils.config import settings
from ....controllers.qkd.bb84.bb84Utils import BB84Utils
from qiskit_aer import Aer
from ....services.quantum_simulator import QuantumSimulator
from ....channels.public_channel import PublicChannel
from ....channels.quantum_channel import QuantumChannel
from ....utils.payload_generate import PayloadGenerator
import logging
logger = logging.getLogger(__name__)

class Sender:
    _instances = {}

    def __new__(cls, key_id, application_id, key_size, quantum_link_info, public_channel_info,manager_callback):
        if key_id not in cls._instances:
            if key_size is None:
                logger.info(f"Key size is not provided for {key_id}, {application_id}")
            cls._instances[key_id] = super(Sender, cls).__new__(cls)
            cls._instances[key_id].__init__(key_id, application_id, key_size, quantum_link_info, public_channel_info,manager_callback)
        return cls._instances[key_id]

    def __init__(self, key_id, application_id, key_size, quantum_link_info, public_channel_info,manager_callback):
        if hasattr(self, 'initialized') and self.initialized:
            return
        
        self.application_id = application_id
        self.key_size = key_size
        self.qubits_requested = key_size * 4
        self.key_id = key_id
        self.matching_bits = None
        self.reveal_bits = None
        self.primary_bases = np.random.randint(2, size=self.qubits_requested)
        self.secondary_bases = None
        self.bits = np.random.randint(2, size=self.qubits_requested)
        self.state = BB84Utils.QuantumProtocolStatus.STARTED
        self.quantum_link_info = quantum_link_info
        self.public_channel_info = public_channel_info
        self.manager_callback = manager_callback
        self.initialized = True

    def __repr__(self):
        return f"<Sender {self.key_id}: {self.application_id}, {self.key_size} bits>"      

    def prepare_qubits(self): 
        qc = QuantumCircuit(self.qubits_requested, self.qubits_requested)  # Create a circuit with 'key_size' qubits
        logger.info(f"starting the BB84 protocol with bits {self.bits}")
        for i in range(self.qubits_requested):
            if self.bits[i] == 1:
                qc.x(i)  # Apply X (bit-flip) gate if the bit is 1
            if self.primary_bases[i] == 1:
                qc.h(i)  # Apply H (Hadamard) gate if the bases is 1
        
        return qc  # Return bits, bases, and the full quantum circuit

    def run_protocol(self):
        if self.state == BB84Utils.QuantumProtocolStatus.STARTED:
            res = PublicChannel.send(self.public_channel_info['target'],PayloadGenerator.protocol_begin("SENDER",self.public_channel_info,self.key_size,self.application_id,BB84Utils.DataEvents.BEGIN,self.key_id))
            if(res):
                self.state = BB84Utils.QuantumProtocolStatus.INITIALIZED
                self.run_protocol()
        if self.state == BB84Utils.QuantumProtocolStatus.INITIALIZED:
            quantum_circuit = self.prepare_qubits()
            rho = self.serialize_circuit(quantum_circuit)
            res = QuantumChannel.send(self.quantum_link_info['target'], PayloadGenerator.send_qubits("SENDER",self.quantum_link_info,self.key_id,BB84Utils.DataEvents.QUBITS,rho))
            if(res):
                self.state = BB84Utils.QuantumProtocolStatus.SENDED_QUBIT
        if self.state == BB84Utils.QuantumProtocolStatus.BASES_RECEIVED:
            res = PublicChannel.send(self.public_channel_info['target'], PayloadGenerator.send_bases("SENDER",self.key_id,BB84Utils.DataEvents.BASES,self.primary_bases))
            if(res):
                matched_bits = [self.bits[i] for i in range(self.qubits_requested) if self.primary_bases[i] == self.secondary_bases[i]]
                if len(matched_bits) < self.qubits_requested/2:
                    logger.info(f"Half of the bases do not match. Discarding transaction....")
                    self.manager_callback(self.key_id,None,self.application_id)
                    self.state=BB84Utils.QuantumProtocolStatus.COMPLETED
                    return  # Discard transaction
            self.matching_bits = matched_bits
            logger.info(f"matching bits on sender end: {self.matching_bits}")
            res = PublicChannel.send(self.public_channel_info['target'], PayloadGenerator.error_correction_bits("SENDER", self.key_id,BB84Utils.DataEvents.ERROR_BITS,self.matching_bits[-int(self.qubits_requested / 4):]))
    
        if self.state == BB84Utils.QuantumProtocolStatus.ERROR_CORRECTION:
            logger.info("Error correction started")
            qber = BB84Utils.calculate_error_rate(self.matching_bits[-int(self.qubits_requested / 4):], self.reveal_bits)
            logger.info(f"QBER: {qber}")
            if qber > settings.ERROR_THRESHOLD:
                logger.info(f"QBER too high. Discarding transaction.")
                self.manager_callback(self.key_id,None,self.application_id)
                self.state=BB84Utils.QuantumProtocolStatus.COMPLETED
                return
            final_key = self.matching_bits[:int(self.qubits_requested / 4)]    
            final_key_str =''.join(map(str, final_key))
            logger.info(f"final key in Sender {final_key_str}")
            self.manager_callback(self.key_id,final_key_str,self.application_id)
            self.state = BB84Utils.QuantumProtocolStatus.COMPLETED
    
    def serialize_circuit(self, qc):
        return dumps(qc)
    def listener(self,data):
        if data['event'] == BB84Utils.DataEvents.BASES:
            self.secondary_bases = data['bases']
            self.state = BB84Utils.QuantumProtocolStatus.BASES_RECEIVED
            self.run_protocol()
        if data['event'] == BB84Utils.DataEvents.ERROR_BITS:
            self.reveal_bits = data['bits']    
            self.state=BB84Utils.QuantumProtocolStatus.ERROR_CORRECTION
            self.run_protocol()