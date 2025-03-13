import socket
import pickle
import numpy as np
import random
import uuid
from enum import Enum,auto
import threading
from qiskit import QuantumCircuit,transpile
from qiskit_aer import Aer
from qiskit_experiments.library import StateTomography
from qiskit.quantum_info import DensityMatrix
from qiskit.quantum_info import Statevector

#from managers.quantum_manager import QuantumManager
from utils.payload_generate import PayloadGenerator

class SenderInstanceFactory:
    _instances = {}

    @staticmethod
    def get_or_create(key_id,connection_id, key_size, quantum_link_info, public_channel_info):
        if key_id not in SenderInstanceFactory._instances:
            if(key_size == None):
                print("Key size is not provided",key_id,connection_id)
            print(key_size)
            SenderInstanceFactory._instances[key_id] = Sender(key_id,connection_id, int(key_size), quantum_link_info, public_channel_info)
        return SenderInstanceFactory._instances[key_id]

def get_public_channel():
    from channels.public_channel import PublicChannel  # Delayed import
    return PublicChannel()  
def get_quantum_channel():
    from channels.quatum_link import QuantumLink  # Delayed import
    return QuantumLink()  
class Sender:
    def __init__(self,key_id,connection_id, key_size,quantum_link_info, public_channel_info):
        self.connection_id =connection_id
        self.aer_sim = Aer.get_backend('qasm_simulator')
        self.key_size = key_size
        self.key_id = key_id
        self.primary_bases = np.random.randint(2, size=key_size)
        self.secondary_bases = None
        self.bits =  np.random.randint(2, size=self.key_size)
        self.state = QuantumProtocolStatus.STARTED
        self.quantum_link_info = quantum_link_info
        self.public_channel_info = public_channel_info
        self.backend = Aer.get_backend('qasm_simulator')



      

    def prepare_qubits(self): 
        qc = QuantumCircuit(self.key_size, self.key_size)  # Create a circuit with 'key_size' qubits

        for i in range(self.key_size):
            if self.bits[i] == 1:
                qc.x(i)  # Apply X (bit-flip) gate if the bit is 1
            if self.primary_bases[i] == 1:
                qc.h(i)  # Apply H (Hadamard) gate if the bases is 1
        
        return qc  # Return bits, bases, and the full quantum circuit

    def run_protocol(self):
        public_channel =get_public_channel();
        quantum_channel =get_quantum_channel();
        if self.state == QuantumProtocolStatus.STARTED:
            res = public_channel.send(self.public_channel_info['target'],PayloadGenerator.protocol_begin("SENDER",self.public_channel_info,self.key_size,self.connection_id,DataEvents.BEGIN,self.key_id))
            if(res):
                self.state = QuantumProtocolStatus.INITIALIZED
                self.run_protocol()
        if self.state == QuantumProtocolStatus.INITIALIZED:
            quantum_circuit = self.prepare_qubits()
            rho = self.perform_tomography(quantum_circuit)
            res = quantum_channel.send(self.quantum_link_info['target'], PayloadGenerator.send_qubits("SENDER",self.quantum_link_info,self.key_id,DataEvents.QUBITS,rho))
            if(res):
                self.state = QuantumProtocolStatus.SENDED_QUBIT
        if self.state == QuantumProtocolStatus.BASES_RECEIVED:
            res = public_channel.send(self.public_channel_info['target'], PayloadGenerator.send_bases("SENDER",self.key_id,DataEvents.BASES,self.primary_bases))
            if(res):
                final_key = [self.bits[i] for i in range(self.key_size) if self.primary_bases[i] == self.secondary_bases[i]]
                from managers.quantum_manager import QuantumManager
                quantum_manager = QuantumManager()  
                quantum_manager.store_key(self.key_id,final_key,self.connection_id)
                self.state = QuantumProtocolStatus.COMPLETED
    
    def perform_tomography(self, qc):
        rho = DensityMatrix.from_instruction(qc) 
        return rho
    def listener(self,data):
        if data['event'] == DataEvents.BASES:
            self.secondary_bases = data['bases']
            self.state = QuantumProtocolStatus.BASES_RECEIVED
            self.run_protocol()

  


class ReceiverInstanceFactory:
    _instances = {}
    @staticmethod
    def get_or_create(key_id,key_size, public_channel_info):
        if key_id not in ReceiverInstanceFactory._instances:
            ReceiverInstanceFactory._instances[key_id] = Receiver(key_id,int(key_size), public_channel_info)
        return ReceiverInstanceFactory._instances[key_id]
    

class Receiver:
    def __init__(self, key_id, key_size, public_channel_info):
        self.key_size = key_size
        self.aer_sim = Aer.get_backend('qasm_simulator')
        self.key_id = key_id
        self.quantum_circuit = None
        self.key_data = None
        self.state = QuantumProtocolStatus.STARTED
        self.primary_bases = np.random.randint(2, size=key_size)
        self.secondary_bases = None
        self.public_channel_info = public_channel_info
          


    def measure_qubits(self,qc, bases):
        num_qubits = qc.num_qubits

        for i in range(num_qubits):
            if bases[i] == 1:
                qc.h(i)  # Apply Hadamard before measuring in the X-bases

        qc.measure_all()


        t_circuit = transpile(qc.reverse_bits(), self.aer_sim)
        counts = self.aer_sim.run(t_circuit, shots=1024).result().get_counts()
        best_outcome = max(counts, key=counts.get)

        return best_outcome  # Return the most likely measurement outcome

    def run_protocol(self):
        public_channel =get_public_channel();
        if self.state == QuantumProtocolStatus.RECEIVED_QUBITS:
            self.key_data = self.measure_qubits(self.quantum_circuit,self.primary_bases)
            res = public_channel.send(self.public_channel_info['source'], PayloadGenerator.send_bases("RECEIVER", self.key_id,DataEvents.BASES,self.primary_bases))
            if(res):
                self.state = QuantumProtocolStatus.BASES_SENT
        if self.state == QuantumProtocolStatus.BASES_RECEIVED:
            final_key = [self.key_data[i] for i in range(self.key_size) if self.primary_bases[i] == self.secondary_bases[i]]
            from managers.quantum_manager import QuantumManager
            quantum_manager = QuantumManager()
            quantum_manager.store_key(self.key_id,final_key)
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

                

    def reconstruct_circuit(self, rho):
        """ Reconstruct a quantum circuit from the given density matrix """
        reconstructed_qc = QuantumCircuit(self.key_size)
        dm = DensityMatrix(rho)  # Convert to Qiskit's DensityMatrix format
        reconstructed_qc.initialize(dm.to_statevector(), list(range(self.key_size)))
        return reconstructed_qc
    


class QuantumProtocolStatus(Enum):
    STARTED = auto()
    SENDED_QUBIT = auto()
    RECEIVING_QUBITS = auto()
    BASES_RECEIVED = auto()
    RECEIVED_QUBITS = auto()
    BASES_SENT = auto()
    COMPLETED = auto()
    INITIALIZED = auto()

class DataEvents(Enum):
    BEGIN = auto()
    BASES = auto()
    QUBITS = auto()
    ABORT = auto()
