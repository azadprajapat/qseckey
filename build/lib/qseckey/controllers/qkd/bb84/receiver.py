import numpy as np
from qiskit import QuantumCircuit,transpile
from qiskit.qasm2 import dumps
from ....controllers.qkd.bb84.bb84Utils import BB84Utils
from ....utils.config import settings
from qiskit_aer import Aer
from ....services.quantum_simulator import QuantumSimulator
from ....channels.public_channel import PublicChannel
from ....channels.quantum_channel import QuantumChannel
from ....utils.payload_generate import PayloadGenerator


class Receiver:
    _instances = {}
    initialized = None

    def __new__(cls, key_id, key_size, public_channel_info,completion_callback=None):
        if key_id not in cls._instances:
            print(f"Creating new Receiver instance as it's a new connection with key_id {key_id}")
            # Create a new instance if not already present
            cls._instances[key_id] = super(Receiver, cls).__new__(cls)
            cls._instances[key_id].__init__(key_id, key_size, public_channel_info,completion_callback)
        return cls._instances[key_id]

    def __init__(self, key_id, key_size, public_channel_info,completion_callback=None):
        if hasattr(self, 'initialized') and self.initialized:
            return
        
        self.qubits_requested = key_size * 4
        self.key_size = key_size
        self.key_id = key_id
        self.quantum_circuit = None
        self.matching_bits = None
        self.reveal_bits = None
        self.key_data = None
        self.state = BB84Utils.QuantumProtocolStatus.STARTED
        self.primary_bases = np.random.randint(2, size=self.qubits_requested)
        self.secondary_bases = None
        self.public_channel_info = public_channel_info
        print("receiver intializatio state",self.initialized, " callback provided",completion_callback)
        self.completion_callback = completion_callback
        self.initialized = True

    def __repr__(self):
        return f"<Receiver {self.key_id}: {self.key_size} bits>"


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
        if self.state == BB84Utils.QuantumProtocolStatus.RECEIVED_QUBITS:
            self.key_data = self.measure_qubits(self.quantum_circuit,self.primary_bases)
            res = PublicChannel.send(self.public_channel_info['source'], PayloadGenerator.send_bases("RECEIVER", self.key_id,BB84Utils.DataEvents.BASES,self.primary_bases))
            if(res):
                self.state = BB84Utils.QuantumProtocolStatus.BASES_SENT
        if self.state == BB84Utils.QuantumProtocolStatus.BASES_RECEIVED:
            matched_bits = [self.key_data[i] for i in range(self.qubits_requested) if self.primary_bases[i] == self.secondary_bases[i]]
            if len(matched_bits) < self.qubits_requested/2:
                print(f"Half of the bases do not match. Discarding transaction.")
                self.state=BB84Utils.QuantumProtocolStatus.COMPLETED
                return  # Discard transaction
            self.matching_bits = matched_bits
            print("matching bits on receiver end:",self.matching_bits)
            res = PublicChannel.send(self.public_channel_info['source'], PayloadGenerator.error_correction_bits("RECEIVER", self.key_id,BB84Utils.DataEvents.ERROR_BITS,self.matching_bits[-int(self.qubits_requested / 4):]))

        if self.state == BB84Utils.QuantumProtocolStatus.ERROR_CORRECTION:
            print("Error correction started")
            qber = BB84Utils.calculate_error_rate(self.matching_bits[-int(self.qubits_requested / 4):], self.reveal_bits)
            print(f"QBER: {qber}")
            if qber > settings.ERROR_THRESHOLD:
                print(f"QBER too high. Discarding transaction.")
                self.state=BB84Utils.QuantumProtocolStatus.COMPLETED
                return  
            final_key = self.matching_bits[:int(self.qubits_requested / 4)]           
            final_key_str =''.join(map(str, final_key))
            print("final key in Receiver",final_key_str)
            self.completion_callback(self.key_id,final_key_str)
            self.state = BB84Utils.QuantumProtocolStatus.COMPLETED

    def listener(self,data):
        if data['event'] == BB84Utils.DataEvents.BEGIN:
            self.key_id = data['key_id']
            self.state = BB84Utils.QuantumProtocolStatus.INITIALIZED
        if data['event'] == BB84Utils.DataEvents.QUBITS:
            self.quantum_circuit = self.reconstruct_circuit(data['qubits'])
            self.state = BB84Utils.QuantumProtocolStatus.RECEIVED_QUBITS
            self.run_protocol()
        if data['event'] == BB84Utils.DataEvents.BASES:
            self.secondary_bases = data['bases']
            self.state = BB84Utils.QuantumProtocolStatus.BASES_RECEIVED
            self.run_protocol()
        if data['event'] == BB84Utils.DataEvents.ERROR_BITS:
            self.reveal_bits = data['bits']
            self.state=BB84Utils.QuantumProtocolStatus.ERROR_CORRECTION
            self.run_protocol()    

                
    def reconstruct_circuit(self, qasm_str):
        return QuantumCircuit.from_qasm_str(qasm_str)