import socket
import pickle
import struct  # Used for packing/unpacking message length
import threading
from utils.config import Settings
from managers.quantum_key_generator import SenderInstanceFactory,ReceiverInstanceFactory

class QuantumLink:
    listener_thread = None
    stop_event = threading.Event()
    server_socket = None
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance exists (Singleton)."""
        if not cls._instance:
            cls._instance = super(QuantumLink, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def send(host, data):
        """Sends data over a simulated quantum link (TCP socket) using length-prefixed messages."""
        host, port = host, Settings.QUANTUM_LISTNER
        serialized_data = pickle.dumps(data)
        data_length = struct.pack("!I", len(serialized_data))  # Pack length as 4 bytes

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                print("Sending data to host and port on quantum link:", host, port)
                s.connect((host, port))
                s.sendall(data_length + serialized_data)  # Send length + data
            return True  # Success
        except (socket.error, Exception) as e:
            print("Error sending data:", e)
            return False  # Failure

    @staticmethod
    def listen(port):
        """Quantum Link listens for incoming data and processes it safely."""
        if QuantumLink.listener_thread and QuantumLink.listener_thread.is_alive():
            print("Listener is already running.")
            return

        def handler():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                QuantumLink.server_socket = s
                s.bind(("", port))
                s.listen()
                print(f"Listening on port {port}...")

                while not QuantumLink.stop_event.is_set():
                    s.settimeout(1.0)  # Allow periodic checks to stop gracefully
                    try:
                        conn, _ = s.accept()
                        with conn:
                            data = QuantumLink._receive_data(conn)  # Safe data reception
                            print("Data received on quantum channel",data)
                            if data:
                                if(data['event'] == 'TEST'):
                                    print("Quantum Channel: Test event received")
                                    return
                                if data.get('source_type') == "SENDER":
                                    receiver = ReceiverInstanceFactory.get_or_create(
                                        data.get('key_id'), "", ""
                                    )
                                    receiver.listener(data)
                                else:
                                    print("Invalid Quantum Data event")
                    except socket.timeout:
                        continue  # Check stop_event and retry

        QuantumLink.stop_event.clear()
        QuantumLink.listener_thread = threading.Thread(target=handler, daemon=True)
        QuantumLink.listener_thread.start()

    @staticmethod
    def _receive_data(conn):
        """Receives length-prefixed data from a socket connection."""
        try:
            # Step 1: Receive the first 4 bytes (data length)
            raw_data_length = conn.recv(4)
            if not raw_data_length:
                return None  # Connection closed

            data_length = struct.unpack("!I", raw_data_length)[0]  # Unpack the length

            # Step 2: Read exactly `data_length` bytes
            received_data = b""
            while len(received_data) < data_length:
                chunk = conn.recv(min(4096, data_length - len(received_data)))
                if not chunk:
                    raise ConnectionError("Connection lost while receiving data")
                received_data += chunk

            return pickle.loads(received_data)  # Deserialize safely

        except (pickle.UnpicklingError, struct.error, ConnectionError) as e:
            print(f"Error receiving data: {e}")
            return None

    @staticmethod
    def stop_listener():
        """Stops the listener thread and closes the socket."""
        QuantumLink.stop_event.set()
        if QuantumLink.server_socket:
            QuantumLink.server_socket.close()
            QuantumLink.server_socket = None
        if QuantumLink.listener_thread:
            QuantumLink.listener_thread.join()
        print("Listener stopped.")
