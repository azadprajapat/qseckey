import json

class KeyStorage:
    _instance = None
    _storage = []  # Shared storage across all instances

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance exists (Singleton)."""
        if not cls._instance:
            cls._instance = super(KeyStorage, cls).__new__(cls)
        return cls._instance

    def save_key(self, key_id, key_data,application_id):
        """Saves a key entry. If key_id exists, it updates the entry."""
        for entry in self._storage:
            if entry["key_id"] == key_id:
                entry["application_id"] = application_id  # Update application_id if needed
                entry["key_data"] = key_data  # Update key_data
                return

        self._storage.append({
            "application_id": application_id,
            "key_id": key_id,
            "key_data": key_data
        })
        print(f"Key {key_id} saved for connection {application_id}")

    def read_keys(self, key_id=None, application_id=None):
        """Retrieves keys based on key_id or application_id. Returns an empty list if nothing is found."""
        if key_id:
            for entry in self._storage:
                if entry["key_id"] == key_id:
                    return [entry]  # Return a list instead of a single dictionary
            return []  # Return an empty list if key_id is not found

        if application_id is not None:
            return [entry for entry in self._storage if entry["application_id"] == application_id]

        return []  # Return an empty list instead of None

    def delete_keys(self, key_id=None, application_id=None):
        """Removes keys by key_id or application_id. Returns False if no parameters passed."""
        if key_id:
            new_storage = [entry for entry in self._storage if entry["key_id"] != key_id]
            if len(new_storage) != len(self._storage):  # Check if anything was removed
                self._storage = new_storage
                return True
            return False  # Key not found

        if application_id is not None:
            new_storage = [entry for entry in self._storage if entry["application_id"] != application_id]
            if len(new_storage) != len(self._storage):  # Check if anything was removed
                self._storage = new_storage
                return True
            return False  # No matching application_id found

        return False  # No action taken

    def to_json(self):
        """Returns the entire storage as a JSON string."""
        return json.dumps(self._storage, indent=2)


