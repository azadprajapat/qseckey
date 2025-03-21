import requests
import json
import time

def register_connection():
    url = "http://localhost:8000/register_connection"
    payload = {
        "source_KME_ID": "sender_app",
        "target_KME_ID": "receiver_app",
        "master_SAE_ID": "ghi",
        "slave_SAE_ID": "jk3",
        "key_size": 512,
        "max_keys_count": 5,
        "max_key_per_request": 1,
        "max_SAE_ID_count": 0
    }
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print("Connection registered successfully.")
    else:
        print("Failed to register connection:", response.text)
    return response.status_code == 200

def get_generated_key():
    url = "http://127.0.0.1:8000/get_key?slave_host=jk3"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print("Key retrieved successfully:", data)
        return data["key_id"], data["key_data"]
    else:
        print("Failed to get key:", response.text)
        return None, None

def verify_key(key_id, expected_key_data):
    url = f"http://127.0.0.1:8001/get_key?key_id={key_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        retrieved_key_data = data.get("key_data")
        if retrieved_key_data == expected_key_data:
            print("Key verification successful: Data matches!")
        else:
            print("Key verification failed: Data mismatch!")
    else:
        print("Failed to verify key:", response.text)

def main():
    if register_connection():
        while True:
            key_id, key_data = get_generated_key()
            time.sleep(2)  # Ensure the key is available in the second server
            if key_id and key_data:
                verify_key(key_id, key_data)
                time.sleep(1)  # Small delay before next iteration

if __name__ == "__main__":
    main()
