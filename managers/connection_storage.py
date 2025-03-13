class ConnectionStorage:
    _instance = None
    _storage = {}  # Shared storage across all instances

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance exists (Singleton)."""
        if not cls._instance:
            cls._instance = super(ConnectionStorage, cls).__new__(cls)
        return cls._instance

    def store_connection(self, connection_id, details):
        """Stores connection details."""
        self._storage[connection_id] = details

    def retrieve_connection(self, connection_id):
        """Retrieves connection details if they exist."""
        return self._storage.get(connection_id)

    def delete_connection(self, connection_id):
        """Deletes a connection if it exists."""
        if connection_id in self._storage:
            del self._storage[connection_id]

    def get_active_connections(self):
        """Returns all active connections that need more keys."""

        return [
            self._storage.get(conn_id) for conn_id in self._storage.keys()
            if self._storage[conn_id]['available_keys_count'] < self._storage[conn_id]['max_keys_count']
        ]


