import socket
import pickle
import numpy as np
import random
import uuid
from enum import Enum,auto
import threading
from qiskit import QuantumCircuit,transpile
from qiskit.qasm2 import dumps
from utils.config import settings
from qiskit_aer import Aer
from managers.quantum_simulator import QuantumSimulator
from channels.public_channel import PublicChannel
from channels.quantum_channel import QuantumChannel

#from managers.quantum_manager import QuantumManager
from utils.payload_generate import PayloadGenerator


def handle_quantum_channel_data(data):
    if(data['event'] == 'TEST'):
        print("Quantum Channel: Test event received")
        return
    if data.get('source_type') == "SENDER":
        receiver = ReceiverInstanceFactory.get_or_create(data.get('key_id'), "", "")
        receiver.listener(data)
    else:
        print("Invalid Quantum Data event")

def handle_public_channel_data(data):
    if data.get('source_type') == "RECEIVER":
        sender = SenderInstanceFactory.get_or_create(
            data.get('key_id'), "", "", "", ""
        )
        sender.listener(data)
    else:
        receiver = ReceiverInstanceFactory.get_or_create(
            data.get('key_id'), data.get('key_size'), data.get('source_host')
        )
        receiver.listener(data)

class QuantumProtocolStatus(Enum):
    STARTED = auto()
    SENDED_QUBIT = auto()
    RECEIVING_QUBITS = auto()
    BASES_RECEIVED = auto()
    ERROR_CORRECTION = auto()
    RECEIVED_QUBITS = auto()
    BASES_SENT = auto()
    KEY_STORAGE = auto()
    COMPLETED = auto()
    INITIALIZED = auto()

class DataEvents(Enum):
    BEGIN = auto()
    BASES = auto()
    QUBITS = auto()
    ERROR_BITS = auto()
    ABORT = auto()


class SenderInstanceFactory:
    _instances = {}

    @staticmethod
    def get_or_create(key_id,application_id, key_size, quantum_link_info, public_channel_info):
        if key_id not in SenderInstanceFactory._instances:
            if(key_size == None):
                print("Key size is not provided",key_id,application_id)
            SenderInstanceFactory._instances[key_id] = Sender(key_id,application_id, int(key_size), quantum_link_info, public_channel_info)
        return SenderInstanceFactory._instances[key_id]

def get_public_channel():
    from channels.public_channel import PublicChannel  # Delayed import
    return PublicChannel()  
def get_quantum_channel():
    from channels.quantum_channel import QuantumChannel  # Delayed import
    return QuantumChannel()  
class Sender:
    def __init__(self,key_id,application_id, key_size,quantum_link_info, public_channel_info):
        self.application_id =application_id
        self.key_size = key_size
        self.qubits_requested = key_size*4
        self.key_id = key_id
        self.matching_bits = None
        self.reveal_bits = None
        self.primary_bases =  np.random.randint(2, size=self.qubits_requested) 
        self.secondary_bases = None
        self.bits =  np.random.randint(2, size=self.qubits_requested)
        self.state = QuantumProtocolStatus.STARTED
        self.quantum_link_info = quantum_link_info
        self.public_channel_info = public_channel_info



      

    def prepare_qubits(self): 
        qc = QuantumCircuit(self.qubits_requested, self.qubits_requested)  # Create a circuit with 'key_size' qubits
        print("starting the protocol with bits",self.bits)
        for i in range(self.qubits_requested):
            if self.bits[i] == 1:
                qc.x(i)  # Apply X (bit-flip) gate if the bit is 1
            if self.primary_bases[i] == 1:
                qc.h(i)  # Apply H (Hadamard) gate if the bases is 1
        
        return qc  # Return bits, bases, and the full quantum circuit

    def run_protocol(self):
        if self.state == QuantumProtocolStatus.STARTED:
            res = PublicChannel.send(self.public_channel_info['target'],PayloadGenerator.protocol_begin("SENDER",self.public_channel_info,self.key_size,self.application_id,DataEvents.BEGIN,self.key_id))
            if(res):
                self.state = QuantumProtocolStatus.INITIALIZED
                self.run_protocol()
        if self.state == QuantumProtocolStatus.INITIALIZED:
            quantum_circuit = self.prepare_qubits()
            rho = self.serialize_circuit(quantum_circuit)
            res = QuantumChannel.send(self.quantum_link_info['target'], PayloadGenerator.send_qubits("SENDER",self.quantum_link_info,self.key_id,DataEvents.QUBITS,rho))
            if(res):
                self.state = QuantumProtocolStatus.SENDED_QUBIT
        if self.state == QuantumProtocolStatus.BASES_RECEIVED:
            res = PublicChannel.send(self.public_channel_info['target'], PayloadGenerator.send_bases("SENDER",self.key_id,DataEvents.BASES,self.primary_bases))
            if(res):
                matched_bits = [self.bits[i] for i in range(self.qubits_requested) if self.primary_bases[i] == self.secondary_bases[i]]
                if len(matched_bits) < self.qubits_requested/2:
                    print(f"Half of the bases do not match. Discarding transaction.")
                    self.state=QuantumProtocolStatus.COMPLETED
                    return  # Discard transaction
            self.matching_bits = matched_bits
            print("matching bits on sender end:",self.matching_bits)
            res = PublicChannel.send(self.public_channel_info['target'], PayloadGenerator.error_correction_bits("SENDER", self.key_id,DataEvents.ERROR_BITS,self.matching_bits[-int(self.qubits_requested / 4):]))
    
        if self.state == QuantumProtocolStatus.ERROR_CORRECTION:
            print("Error correction started")
            qber = calculate_error_rate(self.matching_bits[-int(self.qubits_requested / 4):], self.reveal_bits)
            print(f"QBER: {qber}")
            if qber > settings.ERROR_THRESHOLD:
                print(f"QBER too high. Discarding transaction.")
                self.state=QuantumProtocolStatus.COMPLETED
                return
            final_key = self.matching_bits[:int(self.qubits_requested / 4)]    
            final_key_str =''.join(map(str, final_key))
            print("final key in Sender",final_key_str)
            from managers.quantum_manager import QuantumManager
            quantum_manager = QuantumManager()  
            quantum_manager.store_key(self.key_id,final_key_str,self.application_id)
            self.state = QuantumProtocolStatus.COMPLETED
    
    def serialize_circuit(self, qc):
        return dumps(qc)
    def listener(self,data):
        if data['event'] == DataEvents.BASES:
            self.secondary_bases = data['bases']
            self.state = QuantumProtocolStatus.BASES_RECEIVED
            self.run_protocol()
        if data['event'] == DataEvents.ERROR_BITS:
            self.reveal_bits = data['bits']    
            self.state=QuantumProtocolStatus.ERROR_CORRECTION
            self.run_protocol()

  


class ReceiverInstanceFactory:
    _instances = {}
    @staticmethod
    def get_or_create(key_id,key_size, public_channel_info):
        if key_id not in ReceiverInstanceFactory._instances:
            print("Creating new ReceiverInstanceFactory as its a new connection with key_id",key_id)
            ReceiverInstanceFactory._instances[key_id] = Receiver(key_id,int(key_size), public_channel_info)
        return ReceiverInstanceFactory._instances[key_id]
    
class Receiver:
    def __init__(self, key_id, key_size, public_channel_info):
        self.qubits_requested = key_size*4
        self.key_size = key_size
        self.key_id = key_id
        self.quantum_circuit = None
        self.matching_bits = None
        self.reveal_bits = None
        self.key_data = None
        self.state = QuantumProtocolStatus.STARTED
        self.primary_bases =  np.random.randint(2, size=self.qubits_requested)
        self.secondary_bases = None
        self.public_channel_info = public_channel_info
          


    def measure_qubits(self,qc, bases):
        num_qubits = qc.num_qubits

        for i in range(num_qubits):
            if bases[i] == 1:
                qc.h(i)  # Apply Hadamard before measuring in the X-bases

        qc.measure(range(num_qubits), range(num_qubits))

        print("Max qubits supported: ",settings.NUM_QUBITS)
        print("Qubits provided", num_qubits)
        simulator  = QuantumSimulator()
        counts = simulator.execute_job(qc)  
        best_outcome = max(counts, key=counts.get)  
        max_frequency = counts[best_outcome]  
        max_count = sum(1 for freq in counts.values() if freq == max_frequency)

        print("Best outcome:", best_outcome)
        print("Max frequency:", max_frequency)
        print("Number of outcomes with max frequency:", max_count)
        best_outcome = np.array([int(bit) for bit in best_outcome],dtype=int)
        print("measurement on the quantum simulator completed successfully",best_outcome)

        return best_outcome  # Return the most likely measurement outcome

    def run_protocol(self):
        if self.state == QuantumProtocolStatus.RECEIVED_QUBITS:
            self.key_data = self.measure_qubits(self.quantum_circuit,self.primary_bases)
            res = PublicChannel.send(self.public_channel_info['source'], PayloadGenerator.send_bases("RECEIVER", self.key_id,DataEvents.BASES,self.primary_bases))
            if(res):
                self.state = QuantumProtocolStatus.BASES_SENT
        if self.state == QuantumProtocolStatus.BASES_RECEIVED:
            matched_bits = [self.key_data[i] for i in range(self.qubits_requested) if self.primary_bases[i] == self.secondary_bases[i]]
            if len(matched_bits) < self.qubits_requested/2:
                print(f"Half of the bases do not match. Discarding transaction.")
                self.state=QuantumProtocolStatus.COMPLETED
                return  # Discard transaction
            self.matching_bits = matched_bits
            print("matching bits on receiver end:",self.matching_bits)
            res = PublicChannel.send(self.public_channel_info['source'], PayloadGenerator.error_correction_bits("RECEIVER", self.key_id,DataEvents.ERROR_BITS,self.matching_bits[-int(self.qubits_requested / 4):]))

        if self.state == QuantumProtocolStatus.ERROR_CORRECTION:
            print("Error correction started")
            qber = calculate_error_rate(self.matching_bits[-int(self.qubits_requested / 4):], self.reveal_bits)
            print(f"QBER: {qber}")
            if qber > settings.ERROR_THRESHOLD:
                print(f"QBER too high. Discarding transaction.")
                self.state=QuantumProtocolStatus.COMPLETED
                return  
            final_key = self.matching_bits[:int(self.qubits_requested / 4)]           
            final_key_str =''.join(map(str, final_key))
            print("final key in Receiver",final_key_str)
            from managers.quantum_manager import QuantumManager
            quantum_manager = QuantumManager()
            quantum_manager.store_key(self.key_id,final_key_str)
            self.state = QuantumProtocolStatus.COMPLETED

    def listener(self,data):
        if data['event'] == DataEvents.BEGIN:
            self.key_id = data['key_id']
            self.state = QuantumProtocolStatus.INITIALIZED
        if data['event'] == DataEvents.QUBITS:
            self.quantum_circuit = self.reconstruct_circuit(data['qubits'])
            self.state = QuantumProtocolStatus.RECEIVED_QUBITS
            self.run_protocol()
        if data['event'] == DataEvents.BASES:
            self.secondary_bases = data['bases']
            self.state = QuantumProtocolStatus.BASES_RECEIVED
            self.run_protocol()
        if data['event'] == DataEvents.ERROR_BITS:
            self.reveal_bits = data['bits']
            self.state=QuantumProtocolStatus.ERROR_CORRECTION
            self.run_protocol()    

                
    def reconstruct_circuit(self, qasm_str):
        return QuantumCircuit.from_qasm_str(qasm_str)
    

    


def calculate_error_rate(sender_bits,receiver_bits):
    error_rate = sum([1 for i in range(len(sender_bits)) if sender_bits[i] != receiver_bits[i]]) / len(sender_bits)
    return error_rate