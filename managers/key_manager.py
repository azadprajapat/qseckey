import time
from managers.connection_storage import ConnectionStorage
from managers.key_storage import KeyStorage
from managers.quantum_manager import QuantumManager

class KeyManager:
    def __init__(self):
        self.connection_storage = ConnectionStorage()
        self.key_storage = KeyStorage()
        self.quatum_manager = QuantumManager()
    def create_connection(self, connection_data):
        connection_id = connection_data.get('slave_SAE_ID')
        
        # Check if connection exists
        existing_connection = self.connection_storage.retrieve_connection(connection_id)
        if existing_connection:
            print("Connection already exists")
            return existing_connection
            
        # Create new connection
        connection_data['available_keys_count'] = 0
        self.connection_storage.store_connection(connection_id, connection_data)
        print("Connection created and stored successfully.")
        return connection_data
    def retrieve_connection(self, connection_id):
        """Retrieves connection details for the given connection_id."""
        connection = self.connection_storage.retrieve_connection(connection_id)
        if connection:
            print(f"Connection found for ID {connection_id}")
            return connection
        else:
            print(f"No connection found for ID {connection_id}")
            return None
    def update_connection_data(self, connection_id, key, value):
        """Updates a specific field in the connection data for the given connection_id."""
        connection = self.connection_storage.retrieve_connection(connection_id)
        if connection:
            connection[key] = value
            self.connection_storage.store_connection(connection_id, connection)
            print(f"Updated {key} to {value} for connection {connection_id}")
            return connection
        else:
            print(f"No connection found for ID {connection_id}")
            return None
    def delete_connection(self, connection_id):
        # Delete all keys associated with this connection
        self.key_storage.remove_key(connection_id=connection_id)
        
        # Delete the connection from storage
        self.connection_storage.delete_connection(connection_id)
        print(f"Connection {connection_id} and its associated keys deleted successfully")

    def retrive_key_from_storage(self,key_id,connection_id):
        key = self.key_storage.get_key(key_id,connection_id)
        if key:
            print(f"Key retrieved for ConnectionId {connection_id} and ID {key_id}: {key} ")
            self.key_storage.remove_key(key_id=key["key_id"])
            if(connection_id):
                self.update_key_count_connection(connection_id)
            return key
        else:
            print(f"No key found for  ConnectionId {connection_id} and ID {key_id}")
        return None

    def store_key_in_storage(self, key_id,connection_id, key_data):
        self.key_storage.save_key(key_id,connection_id, key_data)
        if(connection_id):
            self.update_key_count_connection(connection_id)

        print(f"Key stored for ID {key_id}. with connection_id {key_id}")


    def process_connections(self):
        while True:
            connections = self.connection_storage.get_active_connections()
            print("Key manager listening for active connections...")
            for connection in connections:
                print(connection)
              #  QuantumManager.generate_key()
            time.sleep(10)  # Run periodically every 10 seconds

    def update_key_count_connection(self, connection_id):
        """Update the available_keys_count for a connection"""
        keys = self.key_storage.get_key("",connection_id)
        return self.update_connection_data(connection_id, "available_keys_count", len(keys))
