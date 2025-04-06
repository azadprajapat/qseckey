import threading
from typing import Any, Dict, List, Optional

class ConnectionStorage:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConnectionStorage, cls).__new__(cls)
                cls._instance._storage = {}
                cls._instance._storage_lock = threading.Lock()
        return cls._instance

    def create(self, application_id: str, details: Dict[str, Any]) -> None:
        with self._storage_lock:
            self._storage[application_id] = details
            print(f"Connection {application_id} created successfully")
            return details

    def read(self, application_id: Optional[str] = None) -> Optional[Any]:
        with self._storage_lock:
            if application_id is None:
                return list(self._storage.values())
            return self._storage.get(application_id)

    def delete(self, application_id: str) -> bool:
        with self._storage_lock:
            return self._storage.pop(application_id, None) is not None
