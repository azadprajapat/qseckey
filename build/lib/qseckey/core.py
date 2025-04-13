# qkd_key_manager/core.py

from .utils.config import settings
from .controllers.key_manager import KeyManager

key_manager = None

def initialize(config: dict = None):
    global key_manager

    if config:
        for k, v in config.items():
            if hasattr(settings, k):
                setattr(settings, k, v)

    key_manager = KeyManager()

def register_connection(data: dict):
    if not key_manager:
        raise RuntimeError("Library not initialized. Call initialize() first.")
    return key_manager.register_application(data)

def get_key(key_id: str = None, slave_host: str = None, key_size: int = None):
    if not key_manager:
        raise RuntimeError("Library not initialized. Call initialize() first.")
    return key_manager.find_keys(key_id, slave_host, key_size)
