import socket
import pickle
import struct
import threading
from ..utils.config import Settings

class QuantumChannel:
    listener_thread = None
    stop_event = threading.Event()
    server_socket = None
    _handlers = None

    @staticmethod
    def register_handler(handler_fn):
        QuantumChannel._handlers = handler_fn

    @staticmethod
    def send(host, data):
        port = Settings.QUANTUM_LISTNER
        serialized_data = pickle.dumps(data)
        data_length = struct.pack("!I", len(serialized_data))

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                print("Sending data to host and port on quantum link:", host, port)
                s.connect((host, port))
                s.sendall(data_length + serialized_data)
            return True
        except (socket.error, Exception) as e:
            print("Error sending data:", e)
            return False

    @staticmethod
    def listen(port):
        if QuantumChannel.listener_thread and QuantumChannel.listener_thread.is_alive():
            print("Listener is already running.")
            return

        def handler():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                QuantumChannel.server_socket = s
                s.bind(("", port))
                s.listen()
                print(f"Listening on port {port}...")

                while not QuantumChannel.stop_event.is_set():
                    s.settimeout(1.0)
                    try:
                        conn, _ = s.accept()
                        with conn:
                            data = QuantumChannel._receive_data(conn)
                            print("Data received on quantum channel", data)
                            if data and QuantumChannel._handlers:
                                QuantumChannel._handlers(data)
                            elif not QuantumChannel._handlers:
                                print("No handler registered for incoming data.")
                    except socket.timeout:
                        continue

        QuantumChannel.stop_event.clear()
        QuantumChannel.listener_thread = threading.Thread(target=handler, daemon=True)
        QuantumChannel.listener_thread.start()

    @staticmethod
    def _receive_data(conn):
        try:
            raw_data_length = conn.recv(4)
            if not raw_data_length:
                return None

            data_length = struct.unpack("!I", raw_data_length)[0]
            received_data = b""

            while len(received_data) < data_length:
                chunk = conn.recv(min(4096, data_length - len(received_data)))
                if not chunk:
                    raise ConnectionError("Connection lost while receiving data")
                received_data += chunk

            return pickle.loads(received_data)

        except (pickle.UnpicklingError, struct.error, ConnectionError) as e:
            print(f"Error receiving data: {e}")
            return None

    @staticmethod
    def stop_listener():
        QuantumChannel.stop_event.set()
        if QuantumChannel.server_socket:
            QuantumChannel.server_socket.close()
            QuantumChannel.server_socket = None
        if QuantumChannel.listener_thread:
            QuantumChannel.listener_thread.join()
        print("Listener stopped.")
