from fastapi import FastAPI
from utils.routes import router
from utils.config import settings
from managers.key_manager import KeyManager
import uvicorn
import threading


key_manager = KeyManager()
key_manager_thread = threading.Thread(target=key_manager.process_connections, daemon=True)
key_manager_thread.start()

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

# Include Routes
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
    


