import time
from managers.connection_storage import ConnectionStorage
from managers.key_storage import KeyStorage
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
            self.connection_storage = ConnectionStorage()
            self.key_storage = KeyStorage()
            self.initialized = True  
    def create_connection(self, connection_data):
        connection_id = connection_data.get('slave_SAE_ID')

        existing_connection = self.connection_storage.retrieve_connection(connection_id)
        if existing_connection:
            print("Connection already exists")
            return existing_connection

        connection_data['stored_key_count'] = 0
        connection_data['connection_id'] = connection_id
        self.connection_storage.store_connection(connection_id, connection_data)
        from managers.quantum_manager import QuantumManager
        quantum_manager = QuantumManager()
        # quantum_manager.test_connection(connection_data)

        print("Connection created and stored successfully.")
        return connection_data

    def retrieve_connection(self, connection_id):
        connection = self.connection_storage.retrieve_connection(connection_id)
        if connection:
            print(f"Connection found for ID {connection_id}")
            return connection
        print(f"No connection found for ID {connection_id}")
        return None

    def update_connection_data(self, connection_id, key, value):
        connection = self.connection_storage.retrieve_connection(connection_id)
        if connection:
            connection[key] = value
            self.connection_storage.store_connection(connection_id, connection)
            print(f"Updated {key} to {value} for connection {connection_id}")
            return connection
        print(f"No connection found for ID {connection_id}")
        return None

    def delete_connection(self, connection_id):
        self.key_storage.remove_key(connection_id=connection_id)
        self.connection_storage.delete_connection(connection_id)
        print(f"Connection {connection_id} and its associated keys deleted successfully")

    def fetch_key_from_storage(self,key_id,connection_id,key_size):
        if(connection_id):
            connection_data = self.connection_storage.retrieve_connection(connection_id)
            if(connection_data['stored_key_count']<0):
                return "No keys are available currently for the provided slave. Please wait..."
            if(key_size and key_size!=connection_data['key_size']):
                if(key_size%connection_data['key_size']!=0):
                    return "Key size is not a multiple of the connection key size"
                else:
                    return self.merge_and_transmit_keys(key_id,connection_data,connection_id,key_size)

            else:
                return self.retrieve_key_from_storage(key_id,connection_id)
        else:
            return self.retrieve_key_from_storage(key_id,connection_id)

    def merge_and_transmit_keys(self,key_id,connection_data,connection_id,key_size):
        keys_count = key_size//connection_data['key_size']
        if(keys_count>connection_data['stored_key_count']):
            return "Not enough keys available for the requested size"
        key_ids = []
        final_key_id = str(uuid.uuid4())
        final_key = ""
        for i in range(keys_count):
            key = self.retrieve_key_from_storage(key_id,connection_id)
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
            key = self.retrieve_key_from_storage(local_key_id,None)
            if(key == None):
                return "Key not found for the provided key ID"
            final_key += key['key_data']
        self.store_key_in_storage(key_id,final_key,None)
        return "Merged key generated successfully on Receiver KMS"
    def retrieve_key_from_storage(self, key_id, connection_id):
        keys = self.key_storage.get_keys(key_id, connection_id)
        if len(keys) > 0:
            key = keys[0]
            print(f"Key retrieved for Connection ID {connection_id}, Key ID {key_id}: {key}")
            self.key_storage.remove_key(key_id=key["key_id"])
            if connection_id:
                self.update_key_count_connection(connection_id)
            return key
        print(f"No key found for Connection ID {connection_id}, Key ID {key_id}")
        return None

    def store_key_in_storage(self, key_id, key_data,connection_id):
        """Stores a key and updates the connection key count."""
        self.key_storage.save_key(key_id, key_data, connection_id)
        if connection_id:
            self.update_key_count_connection(connection_id)
        print(f"Key stored for ID {key_id} with connection ID {connection_id}")
        print(self.key_storage._storage)

    def process_connections(self):
        """Periodically processes active connections to generate keys."""
        while True:
            from managers.quantum_manager import QuantumManager
            connections = self.connection_storage.get_active_connections()
            print("KeyManager listening for active connections...")
            for connection in connections:
                quantum_manager = QuantumManager()
                quantum_manager.generate_key(connection)
#                self.started=True
            time.sleep(10)  # Run periodically every 10 seconds
            if(self.started):
                break

    def update_key_count_connection(self, connection_id):
        """Updates the stored_key_count for a connection."""
        keys = self.key_storage.get_keys("", connection_id)
        return self.update_connection_data(connection_id, "stored_key_count", len(keys))
