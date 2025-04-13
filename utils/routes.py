from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from controllers.key_manager import KeyManager
from utils.config import settings

router = APIRouter()
key_manager = KeyManager()

@router.post("/register_connection")
def register_connection(connection_data: dict):
    """Registers a new connection with validation."""
    required_params = [
        'source_KME_ID', 'target_KME_ID', 'master_SAE_ID', 'slave_SAE_ID'
    ]

    # Set default key size if not provided
    if connection_data.get('key_size') is None:
        connection_data['key_size'] = settings.DEFAULT_KEY_SIZE
    if connection_data.get('max_keys_count') is None:
        connection_data['max_keys_count']=settings.MAX_KEYS_COUNT
    connection_data['max_key_per_request']=0
    connection_data['max_SAE_ID_count']=0
     
    # Check for missing required parameters
    missing_params = [param for param in required_params if param not in connection_data]
    if missing_params:
        return JSONResponse(
            content={"error": f"Missing required parameters: {', '.join(missing_params)}"},
            status_code=400
        )

    # Validate key size limit
    if connection_data['key_size'] > settings.MAX_KEY_SIZE:
        return JSONResponse(
            content={"error": "Key size exceeds the maximum allowed size"},
            status_code=400
        )

    try:
        connection_response = key_manager.register_application(connection_data)
        return JSONResponse(
            content={"message": "Connection registered successfully", "connection_details": connection_response},
            status_code=201
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to register connection: {str(e)}"},
            status_code=500
        )

@router.get("/get_key")
def get_key(key_id: str = None, slave_host: str = None, key_size: int = None):
    """Retrieves a key from storage."""
    if not key_id and not slave_host:
        return JSONResponse(
            content={"error": "Missing required parameters: key_id or slave_host"},
            status_code=400
        )

    try:
        key_response = key_manager.find_keys(key_id, slave_host, key_size)
        return JSONResponse(content=key_response, status_code=200)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to retrieve key: {str(e)}"},
            status_code=500
        )

@router.post("/generate_merged_key")
def generate_merged_key(payload: dict):
    """Generates a merged key from the provided key IDs."""
    key_id = payload.get('key_id')
    key_ids_payload = payload.get('key_ids_payload')

    if not key_id or not key_ids_payload:
        return JSONResponse(
            content={"error": "Missing required parameters: key_id, key_ids_payload"},
            status_code=400
        )

    try:
        key_manager.prepare_key_receiver(key_id, key_ids_payload)
        return JSONResponse(
            content={"message": "Merged key generated successfully"},
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to generate merged key: {str(e)}"},
            status_code=500
        )

@router.post("/close_connection")
def close_connection(application_id: str):
    """Closes an existing connection."""
    try:
        # Assuming a function exists to handle connection closure
        key_manager.close_connection(application_id)
        return JSONResponse(
            content={"message": "Connection closed successfully"},
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to close connection: {str(e)}"},
            status_code=500
        )
