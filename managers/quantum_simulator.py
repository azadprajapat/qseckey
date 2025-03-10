from abc import ABC, abstractmethod
class QuantumSimulator(ABC):
    @abstractmethod
    def simulate_key_generation(self):
        pass