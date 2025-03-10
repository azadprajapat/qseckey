from fastapi import APIRouter
from managers.key_manager import KeyManager
from utils.config import settings;

router = APIRouter()
key_manager = KeyManager();

@router.post("/register_connection")
def register_connection(connection_data: dict):
    # Validate required parameters
    required_params = ['source_KME_ID', 'target_KME_ID', 'master_SAE_ID', 'slave_SAE_ID', 
                      'key_size', 'max_keys_count', 'max_key_per_request', 'max_SAE_ID_count']
    
    missing_params = [param for param in required_params if param not in connection_data]
    if missing_params:
        return {"error": f"Missing required parameters: {', '.join(missing_params)}"}, 400

    # Create connection
    try:
        connection_response = key_manager.create_connection(connection_data)
        return {
            "message": "Connection registered successfully",
            "connection_details": connection_response
        }
    except Exception as e:
        return {"error": f"Failed to register connection: {str(e)}"}, 500

@router.get("/get_key")
def get_key(key_id: str = None, slave_host: str = None):
    return {"key": "sample_key_data"}

@router.post("/close_connection")
def close_connection(connection_id: str):
    return {"message": "Connection closed successfully"}
