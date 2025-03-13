import os
import base64
from managers.key_manager import KeyManager
import uuid


class QuantumManager:
    _instance = None  # Singleton instance
    #key_manager = KeyManager()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QuantumManager, cls).__new__(cls)

        return cls._instance

    def generate_key(self,connection_info):
        from managers.quantum_simulator import SenderInstanceFactory  # Delayed import
        """Generates a random 256-bit key encoded in base64."""
        print("Quantum manager: generating key...")
        quantum_link_info ={
            "target":connection_info.get('target_KME_ID'),
            "source":connection_info.get('source_KME_ID')
        }
        public_channel_info ={
            "target":connection_info.get('target_KME_ID'),
            "source":connection_info.get('source_KME_ID')
        }

        sender = SenderInstanceFactory.get_or_create(uuid.uuid4(),connection_info.get('connection_id'), connection_info.get('key_size'), quantum_link_info, public_channel_info)
        sender.run_protocol();


    
    def store_key(self, key_id, key_data, connection_id=None):
        """Stores a key with an optional connection_id. key_id is mandatory."""
        from managers.key_manager import KeyManager
        key_manager = KeyManager()

        key_manager.store_key_in_storage(str(key_id),self.binary_array_to_base64(key_data),connection_id);
        print("Quantum Manager: storing the key to the KMS storage")


    import base64

    def binary_array_to_base64(self,binary_array):
        # Convert binary array to bytes
        byte_data = bytes(int("".join(map(str, binary_array[i:i+8])), 2) for i in range(0, len(binary_array), 8))
    
        # Encode bytes to Base64
        base64_encoded = base64.b64encode(byte_data).decode('utf-8')
    
        return base64_encoded