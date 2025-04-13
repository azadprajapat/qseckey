import uuid
import threading
from utils.config import settings
from services.quantum_simulator import QuantumSimulator
from controllers.qkd.bb84.bb84_key_generator import BB84KeyGenerator
from controllers.qkd.bb84.communication_handler import BB84CommunicationHandler
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
        bb84CommunicationHandler = BB84CommunicationHandler(self.store_key)
        PublicChannel.register_handler(bb84CommunicationHandler.handle_public_channel_data)
        QuantumChannel.register_handler(bb84CommunicationHandler.handle_quantum_channel_data)

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
        key_generator = BB84KeyGenerator(uuid.uuid4())
        sender = key_generator.init_sender(
            connection_info.get('application_id'),
            connection_info.get('key_size'),
            quantum_link_info,
            public_channel_info,
            self.store_key
        )
        sender.run_protocol()
        self.key_generation_capacity -= 1

    def store_key(self, key_id, key_data, application_id=None):
        self.key_manager.store_key_in_storage(str(key_id), key_data, application_id)
        print("QuantumManager: storing the key in KMS storage")
        self.key_generation_capacity += 1
