import requests
import json
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import time
SERVER_URL_MASTER = "http://127.0.0.1:8000"
SERVER_URL_SLAVE = "http://127.0.0.1:8001"
import logging
logger = logging.getLogger(__name__)


def register_connection(slave_id):
    """Registers a new connection."""
    payload = {
        "source_KME_ID": "sender_node",
        "target_KME_ID": "receiver_node",
        "master_SAE_ID": "ghi",
        "slave_SAE_ID": slave_id
    }
    
    response = requests.post(f"{SERVER_URL_MASTER}/register_connection", json=payload)
    
    if response.status_code == 200:
        print("Connection registered successfully!")
    else:
        print("Connection already registered successfully!")


def expand_key(bb84_key):
    """Expand a short BB84 key to a 128-bit AES key using SHA-256."""
    key_bytes = bb84_key.encode()  # Convert to bytes
    expanded_key = hashlib.sha256(key_bytes).digest()[:16]  # Take first 16 bytes (128 bits)
    return expanded_key

def get_secure_key(slave_host):
    """Requests a secure key from the SAE server."""
    response = requests.get(f"{SERVER_URL_MASTER}/get_key?slave_host={slave_host}&key_size=128")
    if response.status_code == 200:
        print("Key fetched successfully!")
        return response.json()
    else:
        raise Exception(f"Error fetching key: {response.text}")

def encrypt_message(plain_text, key_data):
    """Encrypts the message using AES CBC mode."""
    key = bytes(int(b) for b in key_data)  # Convert key_data (binary string) to bytes
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv
    encrypted_message = cipher.encrypt(pad(plain_text.encode(), AES.block_size))
    
    return base64.b64encode(iv + encrypted_message).decode()

def decrypt_message(encrypted_message, key_data):
    """Decrypts the message using AES CBC mode."""
    key = bytes(int(b) for b in key_data)
    encrypted_message = base64.b64decode(encrypted_message)
    
    iv = encrypted_message[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    decrypted_message = unpad(cipher.decrypt(encrypted_message[AES.block_size:]), AES.block_size)
    return decrypted_message.decode()

def request_key_from_server(key_id):
    """Slave SAE requests key using key_id."""
    response = requests.get(f"{SERVER_URL_SLAVE}/get_key?key_id={key_id}")
    if response.status_code == 200:
        return response.json()["key_data"]
    else:
        raise Exception(f"Error fetching key by ID: {response.text}")



# Client process
slave_host = "secure_mail_application"
register_connection(slave_host)
print(f"Registered the connection with the slave host {slave_host}")
time.sleep(5)  # Ensure the key is available in the second server

secure_key_response = get_secure_key(slave_host)
key_id = secure_key_response["key_id"]
key_data = secure_key_response["key_data"]
print(f"received the secure key of size from the server {len(key_data)}")
padded_key_data = expand_key(key_data)


message = "Hello, this is BB84 test secure message"

encrypted_msg = encrypt_message(message, padded_key_data)
print(f"Encrypted Message: {encrypted_msg}")

# Simulating Slave SAE receiving encrypted data
retrieved_key_data = request_key_from_server(key_id)
padded_retrieved_key_data = expand_key(retrieved_key_data)
decrypted_msg = decrypt_message(encrypted_msg, padded_retrieved_key_data)

print(f"Decrypted Message: {decrypted_msg}")
