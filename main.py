from fastapi import FastAPI
from utils.routes import router
from utils.config import settings
from managers.key_manager import KeyManager
from managers.quantum_simulator import QuantumSimulator
from channels.public_channel import PublicChannel
from channels.quatum_link import QuantumLink
from qiskit_ibm_runtime import QiskitRuntimeService
import uvicorn
import threading



key_manager = KeyManager()
key_manager_thread = threading.Thread(target=key_manager.process_connections, daemon=True)
key_manager_thread.start()

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

public_channel = PublicChannel()
quantum_channel = QuantumLink()

app.include_router(router)


if __name__ == "__main__":
    print("Saving the account")
    simulator = QuantumSimulator()
    public_thread = threading.Thread(target=public_channel.listen, args=(8081,), daemon=True)
    quantum_thread = threading.Thread(target=quantum_channel.listen, args=(4081,), daemon=True)

    public_thread.start()
    quantum_thread.start()

    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
