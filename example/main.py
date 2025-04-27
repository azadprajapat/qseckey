import os
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import time
from qseckey import initialize, register_connection, get_key  # Assuming these functions exist
import threading
import requests
import logging


logger = logging.getLogger(__name__)
ROLE = os.environ.get("ROLE")

def test_encryption_decryption(key_data,key_id):
    logger.info(f"Sender: Performing encryption with key ID: {key_id} and key data: {key_data}")
    secret_message = "This is a secret message."
    encrypted_message = encrypt_message(secret_message, key_data)
    logger.info(f"Sender: Encrypted message: {encrypted_message}")

    ############# Decryption on Receiver End  with key_id #############

    ###Encryption and decryption are happening within the same process. 
    # In a real distributed scenario, the encrypted message would be sent from the sender container to the 
    # receiver container through a network, and the receiver container would then use the key_id 
    # (obtained through a separate secure channel) to retrieve the key and decrypt the message.####
    secret_key_response = request_key_from_server(key_id=key_id)
    if secret_key_response:
        logger.info(f"Receiver: Key data received for decryption: {secret_key_response}")
        decrypted_message = decrypt_message(encrypted_message, secret_key_response)
        logger.info(f"Receiver: Decrypted message: {decrypted_message}")
    else:
        logger.info(secret_key_response)

    


def encrypt_message(plain_text, key_data):
    key_data=expand_key(key_data)
    """Encrypts the message using AES CBC mode."""
    key = bytes(int(b) for b in key_data)  # Convert key_data (binary string) to bytes
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv
    encrypted_message = cipher.encrypt(pad(plain_text.encode(), AES.block_size))
    
    return base64.b64encode(iv + encrypted_message).decode()


def decrypt_message(encrypted_message, key_data):
    key_data=expand_key(key_data)
    key = bytes(int(b) for b in key_data)
    encrypted_message = base64.b64decode(encrypted_message)
    
    iv = encrypted_message[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    decrypted_message = unpad(cipher.decrypt(encrypted_message[AES.block_size:]), AES.block_size)
    return decrypted_message.decode()


def expand_key(bb84_key):
    """Expand a short BB84 key to a 128-bit AES key using SHA-256."""
    key_bytes = bb84_key.encode()  # Convert to bytes
    expanded_key = hashlib.sha256(key_bytes).digest()[:16]  # Take first 16 bytes (128 bits)
    return expanded_key

def request_key_from_server(key_id):
    """Slave SAE requests key using key_id."""
    response = requests.get(f"http://receiver_node:8000/get_key?key_id={key_id}")
    if response.status_code == 200:
        return response.json()["key_data"]
    else:
        raise Exception(f"Error fetching key by ID: {response.text}")


def main():
    logger.info(f"Running in {ROLE} mode...")
    # Start initialize (and the Uvicorn server) in a separate thread
    server_thread = threading.Thread(target=initialize, daemon=True)
    server_thread.start()
    logger.info("Uvicorn server started in the background.")
    time.sleep(5)  # Give the server a moment to start

    if ROLE == "SENDER":
        target_kme_id = "receiver_node"
        slave_sae_id = "secure_mail_app"
        master_sae_id = "ghi"
        logger.info("waiting for receiver KMS to be up and running...")
        time.sleep(1)
        logger.info(f"Sender: Registering connection...")
        connection_info = register_connection({
            "source_KME_ID": "sender_node",
            "target_KME_ID": target_kme_id,
            "master_SAE_ID": master_sae_id,
            "slave_SAE_ID": slave_sae_id
        })
        if connection_info and "application_id" in connection_info:
            application_id = connection_info["application_id"]
            logger.info(f"Sender: Connection registered with ID: {application_id}")
            logger.info("Sender: Waiting for secure key generation...")
            time.sleep(20)
            key_metadata = get_key(slave_host=slave_sae_id)
            if key_metadata and "key_id" in key_metadata and "key_data" in key_metadata:
                key_id = key_metadata["key_id"]
                key_data = key_metadata["key_data"]
                logger.info(f"Sender: Secure key generated with ID: {key_id}")
                test_encryption_decryption(key_data, key_id)
            else:
                logger.info("Sender: Failed to generate secure key.")
        else:
            logger.info("Sender: Failed to register connection.")

    elif ROLE == "RECEIVER":
        logger.info("Receiver initialized (server started in background).")
        # Receiver-specific logic can go here
        while True:
            time.sleep(1)

if __name__ == "__main__":
    main()




