from enum import Enum, auto

class BB84Utils:
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

    @staticmethod
    def calculate_error_rate(sender_bits, receiver_bits):
        if not sender_bits or not receiver_bits or len(sender_bits) != len(receiver_bits):
            raise ValueError("Bit arrays must be non-empty and of equal length")
        errors = sum(1 for s, r in zip(sender_bits, receiver_bits) if s != r)
        return errors / len(sender_bits)
