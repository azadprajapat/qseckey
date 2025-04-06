import os
import base64
from managers.key_manager import KeyManager
import uuid
from utils.config import settings
from enum import Enum,auto

class QuantumManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance exists (Singleton)."""
        if not cls._instance:
            cls._instance = super(QuantumManager, cls).__new__(cls)
        return cls._instance
    def __init__(self):
        self.key_generation_capacity = settings.KEY_GENERATION_CAPACITY
    def test_connection(self,connection_info):
        print("Quantum manager: testing connection...")
        quantum_link_info ={
            "target":connection_info.get('target_KME_ID'),
            "source":connection_info.get('source_KME_ID')
        }
        public_channel_info ={
            "target":connection_info.get('target_KME_ID'),
            "source":connection_info.get('source_KME_ID')
        }
        from channels.quatum_link import QuantumLink  # Delayed import
        QuantumLink.send(quantum_link_info, {"source_type": "SENDER","event":"TEST"})
        from channels.public_channel import PublicChannel  # Delayed import
        PublicChannel.send(public_channel_info, {"source_type": "SENDER","event":"TEST"})

    def generate_key(self,connection_info):
        if self.key_generation_capacity <= 0:
            print("Quantum manager: key generation capacity reached.")
            return
        from managers.quantum_key_generator import SenderInstanceFactory  # Delayed import
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

        sender = SenderInstanceFactory.get_or_create(uuid.uuid4(),connection_info.get('application_id'), connection_info.get('key_size'), quantum_link_info, public_channel_info)
        sender.run_protocol();
        self.key_generation_capacity -= 1


    
    def store_key(self, key_id, key_data, application_id=None):
        """Stores a key with an optional application_id. key_id is mandatory."""

        from managers.key_manager import KeyManager
        key_manager = KeyManager()

        key_manager.store_key_in_storage(str(key_id),self.binary_array_to_base64(key_data),application_id);
        print("Quantum Manager: storing the key to the KMS storage")
        self.key_generation_capacity += 1


    import base64

    def binary_array_to_base64(self,binary_array):
        # Convert binary array to bytes
        return binary_array
        byte_data = bytes(int("".join(map(str, binary_array[i:i+8])), 2) for i in range(0, len(binary_array), 8))
    
        # Encode bytes to Base64
        base64_encoded = base64.b64encode(byte_data).decode('utf-8')
    
        return base64_encoded