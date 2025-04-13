import uuid
import threading
from utils.config import settings
from managers.quantum_simulator import QuantumSimulator
from managers.quantum_key_generator import (
    handle_public_channel_data,
    handle_quantum_channel_data,
    SenderInstanceFactory,
)
from channels.public_channel import PublicChannel
from channels.quantum_channel import QuantumChannel
import logging

logger = logging.getLogger(__name__)

class QuantumManager:
    _instance = None
    _initialized = False

    def __new__(cls, key_manager=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, key_manager=None):
        if not self.__class__._initialized:
            if key_manager is None:
                raise ValueError("QuantumManager requires a key_manager on first initialization.")
            self._initialize_properties(key_manager)
            self.__class__._initialized = True

    def _initialize_properties(self, key_manager):
        self.key_generation_capacity = settings.KEY_GENERATION_CAPACITY
        self.key_manager = key_manager

        QuantumSimulator()
        PublicChannel.register_handler(handle_public_channel_data)
        QuantumChannel.register_handler(handle_quantum_channel_data)

        threading.Thread(target=PublicChannel.listen, args=(settings.PUBLIC_LISTNER,), daemon=True).start()
        threading.Thread(target=QuantumChannel.listen, args=(settings.QUANTUM_LISTNER,), daemon=True).start()

    def generate_key(self, connection_info):
        if self.key_generation_capacity <= 0:
            print("QuantumManager: key generation capacity reached.")
            return

        logger.info("QuantumManager: generating key...")

        quantum_link_info = {
            "target": connection_info.get('target_KME_ID'),
            "source": connection_info.get('source_KME_ID')
        }

        public_channel_info = {
            "target": connection_info.get('target_KME_ID'),
            "source": connection_info.get('source_KME_ID')
        }

        sender = SenderInstanceFactory.get_or_create(
            uuid.uuid4(),
            connection_info.get('application_id'),
            connection_info.get('key_size'),
            quantum_link_info,
            public_channel_info
        )
        sender.run_protocol()
        self.key_generation_capacity -= 1

    def store_key(self, key_id, key_data, application_id=None):
        self.key_manager.store_key_in_storage(str(key_id), key_data, application_id)
        print("QuantumManager: storing the key in KMS storage")
        self.key_generation_capacity += 1
