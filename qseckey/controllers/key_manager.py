import time
import uuid
from ..services.connection_storage_helper import ConnectionStorageHelper
from ..services.key_storage_helper import KeyStorageHelper
from ..services.request_sender import RequestSender
from ..controllers.qkd.quantum_manager import QuantumManager
from ..utils.config import settings
import threading
import logging
logger = logging.getLogger(__name__)


class KeyManager:
    _instance = None
    started = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.connection_storage_helper = ConnectionStorageHelper()
            self.key_storage_helper = KeyStorageHelper()
            self.quantum_manager = QuantumManager(self)
            self.initialized = True
            process_connection_thread = threading.Thread(target=self.process_connections, daemon=True)
            process_connection_thread.start()

    def register_application(self, connection_data):
        connection_data = self._validateRegisterRequest(connection_data)
        if(self.isReceiverKmsRunning(connection_data)== False):
            raise Exception("Receiver KMS is not running")
        
        return self.connection_storage_helper.store_connection(
            connection_data.get('slave_SAE_ID'), connection_data
        )

    def find_connection(self, application_id):
        connection = self.connection_storage_helper.retrieve_connection(application_id)
        logger.info(f"{'Connection found' if connection else 'No connection found'} for ID {application_id}")
        return connection

    def delete_connection(self, application_id):
        self.connection_storage_helper.delete_connection(application_id)
        logger.info(f"Connection {application_id} and its associated keys deleted successfully")

    def find_keys(self, key_id, application_id, key_size):
        self._validateGetKeyRequest(key_id,application_id)
        if not application_id:
            return self.key_storage_helper.retrieve_key_from_storage(key_id, application_id)
        
        conn = self.connection_storage_helper.retrieve_connection(application_id)
        if not conn:
            return "No connection found for the provided application ID"
        if conn['stored_key_count'] < 0:
            return "No keys are available currently for the provided slave. Please wait..."
        if key_size and key_size != conn['key_size']:
            if key_size % conn['key_size']:
                return "Key size is not a multiple of the connection key size"
            return self.__merge_and_transmit_keys(key_id, conn, application_id, key_size)
        return self.key_storage_helper.retrieve_key_from_storage(key_id, application_id)

    def __merge_and_transmit_keys(self, key_id, conn, application_id, key_size):
        start_time = time.time()
        count = key_size // conn['key_size']
        if count > conn['stored_key_count']:
            return "Not enough keys available for the requested size"

        final_key_id = str(uuid.uuid4())
        key_ids, final_key = [], ""
        for _ in range(count):
            key = self.key_storage_helper.retrieve_key_from_storage(key_id, application_id)
            key_ids.append(key['key_id'])
            final_key += key['key_data']

        res = self._httpSender(conn).post("/generate_merged_key", json={"key_id": final_key_id, "key_ids_payload": key_ids})
        end_time = time.time()
        elapsed_time = (end_time - start_time)
        logger.info(f"Key merging and reconciliation with receiver completed in {elapsed_time:.2f} seconds.")
        return {'key_id': final_key_id, 'key_data': final_key} if res.status_code == 200 else "Failed to generate key"

    def prepare_key_receiver(self, key_id, key_ids_payload):
        final_key = ""
        for kid in key_ids_payload:
            key = self.key_storage_helper.retrieve_key_from_storage(kid, None)
            if not key:
                return "Key not found for the provided key ID"
            final_key += key['key_data']
        self.key_storage_helper.store_key_in_storage(key_id, final_key, None)
        return "Merged key generated successfully on Receiver KMS"

    def store_key_in_storage(self, key_id, key_data, application_id):
        self.key_storage_helper.store_key_in_storage(key_id, key_data, application_id)
        logger.info(f"Key stored for ID {key_id} with connection ID {application_id}")

    def isReceiverKmsRunning(self,connection_info):
        res = self._httpSender(connection_info).get("/ping")
        if res and res.status_code == 200:
            logger.info(f"Receiver KMS is up and running")
            return True
        else:
            logger.info(f"Receiver KMS is not running")
            return False

    def process_connections(self):
        while True:
            connections = self.connection_storage_helper.get_active_connections()
            for conn in connections:
                self.quantum_manager.generate_key(conn)
            time.sleep(10)
            if self.started:
                break
   
    def _httpSender(self,connection_info):
        target_kme_id = connection_info.get('target_KME_ID')
        httpSender = RequestSender(f"http://{target_kme_id}:{settings.PORT}")
        return httpSender
    
    def _validateRegisterRequest(self,connection_data):
        required_params = [
        'source_KME_ID', 'target_KME_ID', 'master_SAE_ID', 'slave_SAE_ID']
        if connection_data.get('key_size') is None:
            connection_data['key_size'] = settings.DEFAULT_KEY_SIZE
        if connection_data.get('max_keys_count') is None:
            connection_data['max_keys_count']=settings.MAX_KEYS_COUNT
        connection_data['max_key_per_request']=0
        connection_data['max_SAE_ID_count']=0
     
        missing_params = [param for param in required_params if param not in connection_data]
        if missing_params:
            raise Exception(f"Missing required parameters: {', '.join(missing_params)}")

        if connection_data['key_size'] > settings.MAX_KEY_SIZE:
            raise Exception(f"Key size exceeds the maximum allowed size:",settings.MAX_KEY_SIZE)
        return connection_data
    
    def _validateGetKeyRequest(self,key_id,slave_host):
        if not key_id and not slave_host:
            raise Exception(f"Missing required parameters: key_id or slave_host:",settings.MAX_KEY_SIZE)
