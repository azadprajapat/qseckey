class Settings:
    PROJECT_NAME = "QKD Key Management System"
    PROJECT_VERSION = "1.0.0"
    HOST = "0.0.0.0"
    PORT = 8000
    NUM_QUBITS = 28
    MAX_KEY_SIZE = NUM_QUBITS/2   
    PUBLIC_LISTNER = 8081
    QUANTUM_LISTNER = 4081
    DEBUG = True
    

settings = Settings()
