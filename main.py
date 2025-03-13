from fastapi import FastAPI
from utils.routes import router
from utils.config import settings
from managers.key_manager import KeyManager
from channels.public_channel import PublicChannel
from channels.quatum_link import QuantumLink
import uvicorn
import threading


key_manager = KeyManager()
key_manager_thread = threading.Thread(target=key_manager.process_connections, daemon=True)
key_manager_thread.start()


app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

public_channel = PublicChannel();
quantum_channel = QuantumLink();
# Include Routes
app.include_router(router)

import threading
import uvicorn

if __name__ == "__main__":
    # Start Uvicorn in a separate thread
    server_thread = threading.Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={"host": settings.HOST, "port": settings.PORT},
        daemon=True
    )
    server_thread.start()

    # Start listeners
    public_channel.listen(8081)
    quantum_channel.listen(4081)

    # Keep the main thread alive
    server_thread.join()

    


