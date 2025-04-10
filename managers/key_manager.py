import time
import uuid
from services.connection_storage_helper import ConnectionStorageHelper
from services.key_storage_helper import KeyStorageHelper
from services.request_sender import RequestSender
from utils.config import settings

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
            self.initialized = True

    def register_application(self, connection_data):
        return self.connection_storage_helper.store_connection(
            connection_data.get('slave_SAE_ID'), connection_data
        )

    def find_connection(self, application_id):
        connection = self.connection_storage_helper.retrieve_connection(application_id)
        print(f"{'Connection found' if connection else 'No connection found'} for ID {application_id}")
        return connection

    def delete_connection(self, application_id):
        self.connection_storage_helper.delete_connection(application_id)
        print(f"Connection {application_id} and its associated keys deleted successfully")

    def find_keys(self, key_id, application_id, key_size):
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
        count = key_size // conn['key_size']
        if count > conn['stored_key_count']:
            return "Not enough keys available for the requested size"

        final_key_id = str(uuid.uuid4())
        key_ids, final_key = [], ""
        for _ in range(count):
            key = self.key_storage_helper.retrieve_key_from_storage(key_id, application_id)
            key_ids.append(key['key_id'])
            final_key += key['key_data']

        sender = RequestSender(f"http://{conn['target_KME_ID']}:{settings.PORT}")
        res = sender.post("/generate_merged_key", json={"key_id": final_key_id, "key_ids_payload": key_ids})
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
        print(f"Key stored for ID {key_id} with connection ID {application_id}")

    def process_connections(self):
        from managers.quantum_manager import QuantumManager
        while True:
            connections = self.connection_storage_helper.get_active_connections()
            print("KeyManager listening for active connections...")
            for conn in connections:
                QuantumManager().generate_key(conn)
            time.sleep(10)
            if self.started:
                break
