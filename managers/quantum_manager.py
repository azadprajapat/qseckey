import os
import base64
from managers.key_manager import KeyManager

class QuantumManager:
    _instance = None  # Singleton instance
    key_manager = KeyManager()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QuantumManager, cls).__new__(cls)
        return cls._instance

    def generate_key(self):
        """Generates a random 256-bit key encoded in base64."""
        print("Quantum manager: generating key...")
        key = os.urandom(32)  # 256-bit random key
        return base64.b64encode(key).decode()  # Convert to a readable format

    def store_key(self, key_id, key_data, connection_id=None):
        """Stores a key with an optional connection_id. key_id is mandatory."""
        self.key_manager.store_key_in_storage(self,key_id,connection_id,key_data);
        print("Quantum Manager: storing the key to the KMS storage")
