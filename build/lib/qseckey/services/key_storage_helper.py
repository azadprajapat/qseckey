
from ..services.storage.key_storage import KeyStorage
class KeyStorageHelper:
    _instance = None  
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(KeyStorageHelper, cls).__new__(cls)
        return cls._instance
    def __init__(self):
        if not hasattr(self, 'initialized'):  
            self.key_storage = KeyStorage()
            self.initialized = True    

    def retrieve_key_from_storage(self, key_id, application_id):
        keys = self.key_storage.read_keys(key_id, application_id)
        if len(keys) > 0:
            key = keys[0]
            print(f"Key retrieved for Connection ID {application_id}, Key ID {key_id}: {key}")
            self.key_storage.delete_keys(key_id=key["key_id"])
            return key
        print(f"No key found for Connection ID {application_id}, Key ID {key_id}")
        return None
    def storage_key_count(self,application_id):
        return len(self.key_storage.read_keys(application_id=application_id))

    def store_key_in_storage(self, key_id, key_data,application_id):
        """Stores a key and updates the connection key count."""
        self.key_storage.save_key(key_id, key_data, application_id)
        print(f"Key stored for ID {key_id} with connection ID {application_id}")
        print(self.key_storage._storage)
    
    def delete_key_in_storage(self,key_id=None,application_id=None):
        self.key_storage.delete_keys(key_id,application_id)