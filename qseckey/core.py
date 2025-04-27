import logging
from .utils.config import settings
from .controllers.key_manager import KeyManager
from fastapi import FastAPI
import uvicorn
from .routes import router  # Import the router

logger = logging.getLogger(__name__)
key_manager = None
app = None  # Global app instance

def initialize(config: dict = None):

    global key_manager, app
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    if config:
        for k, v in config.items():
            if hasattr(settings, k):
                setattr(settings, k, v)
    key_manager = KeyManager()

    app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
    app.include_router(router)
    run_server()

def run_server():
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)

def register_connection(data: dict):
    if not key_manager:
        raise RuntimeError("Library not initialized. Call initialize() first.")
    return key_manager.register_application(data)

def get_key(key_id: str = None, slave_host: str = None, key_size: int = None):
    if not key_manager:
        raise RuntimeError("Library not initialized. Call initialize() first.")
    return key_manager.find_keys(key_id, slave_host, key_size)