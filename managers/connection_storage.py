class ConnectionStorage:
    _instance = None
    _storage = {}  
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConnectionStorage, cls).__new__(cls)
        return cls._instance

    def store_connection(self, connection_id, details):
        self._storage[connection_id] = details

    def retrieve_connection(self, connection_id):
        return self._storage.get(connection_id)

    def delete_connection(self, connection_id):
        if connection_id in self._storage:
            del self._storage[connection_id]

    def get_active_connections(self):

        return [
            self._storage.get(conn_id) for conn_id in self._storage.keys()
            if self._storage[conn_id]['stored_key_count'] < self._storage[conn_id]['max_keys_count']
        ]


