import socket
import pickle
import numpy as np
import random
import uuid
from enum import Enum,auto
import threading
from qiskit import QuantumCircuit,transpile
from qiskit.qasm2 import dumps
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
        self.key_size = key_size
        self.key_id = key_id
        self.primary_bases =  np.random.randint(2, size=self.key_size) 
        self.secondary_bases = None
        self.bits =  np.random.randint(2, size=self.key_size)
        self.state = QuantumProtocolStatus.STARTED
        self.quantum_link_info = quantum_link_info
        self.public_channel_info = public_channel_info



      

    def prepare_qubits(self): 
        qc = QuantumCircuit(self.key_size, self.key_size)  # Create a circuit with 'key_size' qubits
        print("starting the protocol with bits",self.bits)
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
            rho = self.serialize_circuit(quantum_circuit)
            res = quantum_channel.send(self.quantum_link_info['target'], PayloadGenerator.send_qubits("SENDER",self.quantum_link_info,self.key_id,DataEvents.QUBITS,rho))
            if(res):
                self.state = QuantumProtocolStatus.SENDED_QUBIT
        if self.state == QuantumProtocolStatus.BASES_RECEIVED:
            res = public_channel.send(self.public_channel_info['target'], PayloadGenerator.send_bases("SENDER",self.key_id,DataEvents.BASES,self.primary_bases))
            if(res):
                final_key = [self.bits[i] for i in range(self.key_size) if self.primary_bases[i] == self.secondary_bases[i]]
                final_key_str =''.join(map(str, final_key))
                print("final key in Sender",final_key_str)
                from managers.quantum_manager import QuantumManager
                quantum_manager = QuantumManager()  
                quantum_manager.store_key(self.key_id,final_key_str,self.connection_id)
                self.state = QuantumProtocolStatus.COMPLETED
    
    def serialize_circuit(self, qc):
        return dumps(qc)
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
            print("Creating new ReceiverInstanceFactory as its a new connection with key_id",key_id)
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
        self.primary_bases =  np.random.randint(2, size=self.key_size)
        self.secondary_bases = None
        self.public_channel_info = public_channel_info
          


    def measure_qubits(self,qc, bases):
        num_qubits = qc.num_qubits

        for i in range(num_qubits):
            if bases[i] == 1:
                qc.h(i)  # Apply Hadamard before measuring in the X-bases

        qc.measure(range(num_qubits), range(num_qubits))

        print("Max qubits supported: ",self.aer_sim.configuration().n_qubits)
        print("Qubits provided", num_qubits)

        transpiled_qc = transpile(qc.reverse_bits(), self.aer_sim)
        counts = self.aer_sim.run(transpiled_qc, shots=2048).result().get_counts()
        best_outcome = max(counts, key=counts.get)
        max_frequency = max(counts.values())


        max_count = sum(1 for freq in counts.values() if freq == max_frequency)

        print("Number of outcomes with maximum frequency: ",max_frequency," and count ", max_count)
        best_outcome = np.array([int(bit) for bit in best_outcome],dtype=int)
        print("measurement on the quantum simulator complted successfully",best_outcome)

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

                
    def reconstruct_circuit(self, qasm_str):
        return QuantumCircuit.from_qasm_str(qasm_str)
    


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
