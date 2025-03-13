import socket
import pickle
import struct  # Used for packing/unpacking message length
import threading
from managers.quantum_simulator import SenderInstanceFactory, ReceiverInstanceFactory

class PublicChannel:
    listener_thread = None
    stop_event = threading.Event()
    server_socket = None
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance exists (Singleton)."""
        if not cls._instance:
            cls._instance = super(PublicChannel, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def send(connection_info, data):
        """Sends data over a classical public channel (TCP socket) using length-prefixed messages."""
        host, port = connection_info['target'], 8081
        serialized_data = pickle.dumps(data)
        data_length = struct.pack("!I", len(serialized_data))  # Pack length as 4 bytes

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(data_length + serialized_data)  # Send length + data

    @staticmethod
    def listen(port):
        """Listens for incoming data and processes it safely using length-prefixed protocol."""
        if PublicChannel.listener_thread and PublicChannel.listener_thread.is_alive():
            print("Public channel Listener is already running.")
            return

        def handler():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                PublicChannel.server_socket = s
                s.bind(("", port))
                s.listen()
                print(f"Listening on port {port}...")

                while not PublicChannel.stop_event.is_set():
                    s.settimeout(1.0)  # Allow periodic checks to stop gracefully
                    try:
                        conn, _ = s.accept()
                        with conn:
                            data = PublicChannel._receive_data(conn)  # Safe data reception
                            if data:
                                if data.get('source_type') == "RECEIVER":
                                    sender = SenderInstanceFactory.get_or_create(
                                        data.get('key_id'), "", "", "", ""
                                    )
                                    sender.listener(data)
                                else:
                                    receiver = ReceiverInstanceFactory.get_or_create(
                                        data.get('key_id'), data.get('key_size'), data.get('source_host')
                                    )
                                    receiver.listener(data)
                    except socket.timeout:
                        continue  # Check stop_event and retry

        PublicChannel.stop_event.clear()
        PublicChannel.listener_thread = threading.Thread(target=handler, daemon=True)
        PublicChannel.listener_thread.start()

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
        PublicChannel.stop_event.set()
        if PublicChannel.server_socket:
            PublicChannel.server_socket.close()
            PublicChannel.server_socket = None
        if PublicChannel.listener_thread:
            PublicChannel.listener_thread.join()
        print("Listener stopped.")
