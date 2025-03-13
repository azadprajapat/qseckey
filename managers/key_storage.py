import json

class KeyStorage:
    _instance = None
    _storage = []  # Shared storage across all instances

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance exists (Singleton)."""
        if not cls._instance:
            cls._instance = super(KeyStorage, cls).__new__(cls)
        return cls._instance

    def save_key(self, key_id, key_data,connection_id):
        """Saves a key entry. If key_id exists, it updates the entry."""
        for entry in self._storage:
            if entry["key_id"] == key_id:
                entry["connection_id"] = connection_id  # Update connection_id if needed
                entry["key_data"] = key_data  # Update key_data
                return

        self._storage.append({
            "connection_id": connection_id,
            "key_id": key_id,
            "key_data": key_data
        })
        print(f"Key {key_id} saved for connection {connection_id}")

    def get_key(self, key_id=None, connection_id=None):
        """Retrieves keys based on key_id or connection_id. Returns empty if nothing passed."""
        if key_id:
            for entry in self._storage:
                if entry["key_id"] == key_id:
                    return entry
            return None  # Key not found

        if connection_id is not None:
            result = [entry for entry in self._storage if entry["connection_id"] == connection_id]
            return result if result else None  # Return None if no matches

        return None  # Return None if no parameters are given

    def remove_key(self, key_id=None, connection_id=None):
        """Removes keys by key_id or connection_id. Returns False if no parameters passed."""
        if key_id:
            new_storage = [entry for entry in self._storage if entry["key_id"] != key_id]
            if len(new_storage) != len(self._storage):  # Check if anything was removed
                self._storage = new_storage
                return True
            return False  # Key not found

        if connection_id is not None:
            new_storage = [entry for entry in self._storage if entry["connection_id"] != connection_id]
            if len(new_storage) != len(self._storage):  # Check if anything was removed
                self._storage = new_storage
                return True
            return False  # No matching connection_id found

        return False  # No action taken

    def to_json(self):
        """Returns the entire storage as a JSON string."""
        return json.dumps(self._storage, indent=2)


