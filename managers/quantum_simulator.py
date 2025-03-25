import time
from utils.config import settings
from qiskit import transpile
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit_aer import Aer

class QuantumSimulator:
    _instance = None  
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QuantumSimulator, cls).__new__(cls)

        return cls._instance
    
    def __init__(self):
        QiskitRuntimeService.save_account(channel='ibm_quantum',token=settings.IBM_TOKEN,overwrite=True)
        service = QiskitRuntimeService()
        #self.backend = service.backend('ibm_kyiv')
        self.backend =Aer.get_backend('qasm_simulator')


    # def execute_job(self,qc):
    #     pm = generate_preset_pass_manager(backend=self.backend, optimization_level=1)
    #     isa_circuit = pm.run(qc)

    #     sampler = Sampler(mode=self.backend)
    #     sampler.options.default_shots = 1024 
    #     print("Running the circuit on the backend")
    #     job = sampler.run([isa_circuit])
    #     print(f"Job ID is {job.job_id()}")
    #     pub_result = job.result()[0]
    #     print(pub_result.data)
    #     counts = pub_result.data.c.get_counts()
    #     return counts
    
    def execute_job(self,qc):

        transpiled_qc = transpile(qc.reverse_bits(), self.backend)
        counts = self.backend.run(transpiled_qc, shots=2048).result().get_counts()
        return counts

    

    