import time
from services.connection_storage_helper import ConnectionStorageHelper
from services.key_storage_helper import KeyStorageHelper
from utils.config import settings
from services.request_sender import RequestSender
import uuid

class KeyManager:
    _instance = None  
    started=False


    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(KeyManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):  
            self.connection_storage_helper = ConnectionStorageHelper()
            self.key_storage_helper = KeyStorageHelper()
            self.initialized = True  
    def register_application(self, connection_data):
        application_id = connection_data.get('slave_SAE_ID')
        return  self.connection_storage_helper.store_connection(application_id, connection_data)

    def retrieve_connection(self, application_id):
        connection = self.connection_storage_helper.retrieve_connection(application_id)
        if connection:
            print(f"Connection found for ID {application_id}")
            return connection
        print(f"No connection found for ID {application_id}")
        return None

    def delete_connection(self, application_id):
        self.connection_storage_helper.delete_connection(application_id)
        print(f"Connection {application_id} and its associated keys deleted successfully")

    def fetch_key_from_storage(self,key_id,application_id,key_size):
        if(application_id):
            connection_data = self.connection_storage_helper.retrieve_connection(application_id)
            if not connection_data:
                return "No connection found for the provided application ID"
            if(connection_data['stored_key_count']<0):
                return "No keys are available currently for the provided slave. Please wait..."
            if(key_size and key_size!=connection_data['key_size']):
                if(key_size%connection_data['key_size']!=0):
                    return "Key size is not a multiple of the connection key size"
                else:
                    return self.merge_and_transmit_keys(key_id,connection_data,application_id,key_size)

            else:
                return self.key_storage_helper.retrieve_key_from_storage(key_id,application_id)
        else:
            return self.key_storage_helper.retrieve_key_from_storage(key_id,application_id)

    def merge_and_transmit_keys(self,key_id,connection_data,application_id,key_size):
        keys_count = key_size//connection_data['key_size']
        if(keys_count>connection_data['stored_key_count']):
            return "Not enough keys available for the requested size"
        key_ids = []
        final_key_id = str(uuid.uuid4())
        final_key = ""
        for i in range(keys_count):
            key = self.key_storage_helper.retrieve_key_from_storage(key_id,application_id)
            key_ids.append(key['key_id'])
            final_key += key['key_data']
        sender = RequestSender(base_url="http://" + connection_data['target_KME_ID'] + ":" + str(settings.PORT))
        res = sender.post("/generate_merged_key", json={"key_id": final_key_id, "key_ids_payload": key_ids})
        if(res.status_code==200):
            return {'key_id':final_key_id,'key_data': final_key}
        else:
            return "Failed to generate key"
        return 

    def merge_and_prepare_final_key_slave(self,key_id,key_ids_payload):
        final_key = ""
        for local_key_id in key_ids_payload:
            key = self.key_storage_helper.retrieve_key_from_storage(local_key_id,None)
            if(key == None):
                return "Key not found for the provided key ID"
            final_key += key['key_data']
        self.key_storage_helper.store_key_in_storage(key_id,final_key,None)
        return "Merged key generated successfully on Receiver KMS"
    
    def store_key_in_storage(self, key_id, key_data,application_id):
        """Stores a key and updates the connection key count."""
        self.key_storage_helper.store_key_in_storage(key_id, key_data, application_id)
        print(f"Key stored for ID {key_id} with connection ID {application_id}")

    def process_connections(self):
        """Periodically processes active connections to generate keys."""
        while True:
            from managers.quantum_manager import QuantumManager
            connections = self.connection_storage_helper.get_active_connections()
            print("KeyManager listening for active connections...")
            for connection in connections:
                quantum_manager = QuantumManager()
                quantum_manager.generate_key(connection)
#                self.started=True
            time.sleep(10)  # Run periodically every 10 seconds
            if(self.started):
                break
