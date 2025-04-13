import threading
import logging
import uuid

from qseckey.utils.config import settings
from qseckey.services.quantum_simulator import QuantumSimulator
from qseckey.controllers.qkd.bb84.bb84_key_generator import BB84KeyGenerator
from qseckey.controllers.qkd.bb84.communication_handler import BB84CommunicationHandler
from qseckey.channels.public_channel import PublicChannel
from qseckey.channels.quantum_channel import QuantumChannel

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
                raise ValueError("QuantumManager requires a KeyManager instance on first initialization.")
            self._setup(key_manager)
            self.__class__._initialized = True

    def _setup(self, key_manager):
        self.key_generation_capacity = settings.KEY_GENERATION_CAPACITY
        self.key_manager = key_manager

        QuantumSimulator()

        comm_handler = BB84CommunicationHandler(self.store_key)
        PublicChannel.register_handler(comm_handler.handle_public_channel_data)
        QuantumChannel.register_handler(comm_handler.handle_quantum_channel_data)

        threading.Thread(target=PublicChannel.listen, args=(settings.PUBLIC_LISTNER,), daemon=True).start()
        threading.Thread(target=QuantumChannel.listen, args=(settings.QUANTUM_LISTNER,), daemon=True).start()

        logger.info("QuantumManager initialized and channels are now listening.")

    def generate_key(self, connection_info: dict):
        if self.key_generation_capacity <= 0:
            logger.warning("Key generation capacity reached.")
            return

        key_id = uuid.uuid4()
        logger.info(f"Starting key generation for key_id={key_id}")
        key_generator = BB84KeyGenerator(key_id,self.store_key)
        key_generator.init_key_generation(connection_info)

        self.key_generation_capacity -= 1

    def store_key(self, key_id, key_data, application_id=None):
        """Store generated key into the KeyManager's storage."""
        logger.info(f"Storing key {key_id} in KMS storage.")
        self.key_manager.store_key_in_storage(str(key_id), key_data, application_id)
        self.key_generation_capacity += 1
