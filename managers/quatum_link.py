from abc import ABC, abstractmethod
class QuantumLink(ABC):
    @abstractmethod
    def transmit_key(self, key_data):
        pass