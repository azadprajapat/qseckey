import time
from managers.connection_storage import ConnectionStorage
from managers.key_storage import KeyStorage

class KeyManager:
    _instance = None  # Class-level variable to store the singleton instance

    def __new__(cls, *args, **kwargs):
        """Ensures only one instance of KeyManager exists."""
        if not cls._instance:
            cls._instance = super(KeyManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):  # Prevent re-initialization
            self.connection_storage = ConnectionStorage()
            self.key_storage = KeyStorage()
            self.initialized = True  # Mark as initialized

    def create_connection(self, connection_data):
        """Creates or retrieves an existing connection."""
        connection_id = connection_data.get('slave_SAE_ID')

        existing_connection = self.connection_storage.retrieve_connection(connection_id)
        if existing_connection:
            print("Connection already exists")
            return existing_connection

        connection_data['available_keys_count'] = 0
        connection_data['connection_id'] = connection_id
        self.connection_storage.store_connection(connection_id, connection_data)
        from managers.quantum_manager import QuantumManager
        quantum_manager = QuantumManager()
        # quantum_manager.test_connection(connection_data)

        print("Connection created and stored successfully.")
        return connection_data

    def retrieve_connection(self, connection_id):
        """Retrieves connection details for the given connection_id."""
        connection = self.connection_storage.retrieve_connection(connection_id)
        if connection:
            print(f"Connection found for ID {connection_id}")
            return connection
        print(f"No connection found for ID {connection_id}")
        return None

    def update_connection_data(self, connection_id, key, value):
        """Updates a specific field in the connection data."""
        connection = self.connection_storage.retrieve_connection(connection_id)
        if connection:
            connection[key] = value
            self.connection_storage.store_connection(connection_id, connection)
            print(f"Updated {key} to {value} for connection {connection_id}")
            return connection
        print(f"No connection found for ID {connection_id}")
        return None

    def delete_connection(self, connection_id):
        """Deletes a connection and its associated keys."""
        self.key_storage.remove_key(connection_id=connection_id)
        self.connection_storage.delete_connection(connection_id)
        print(f"Connection {connection_id} and its associated keys deleted successfully")

    def retrieve_key_from_storage(self, key_id, connection_id):
        """Retrieves and removes a key from storage."""
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
            time.sleep(10)  # Run periodically every 10 seconds

    def update_key_count_connection(self, connection_id):
        """Updates the available_keys_count for a connection."""
        keys = self.key_storage.get_keys("", connection_id)
        return self.update_connection_data(connection_id, "available_keys_count", len(keys))
