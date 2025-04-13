import socket
import pickle
import struct
import threading
from qseckey.utils.config import Settings

class PublicChannel:
    listener_thread = None
    stop_event = threading.Event()
    server_socket = None
    message_handler = None

    @staticmethod
    def register_handler(callback):
        PublicChannel.message_handler = callback

    @staticmethod
    def send(host, data):
        port = Settings.PUBLIC_LISTNER
        serialized_data = pickle.dumps(data)
        data_length = struct.pack("!I", len(serialized_data))

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                print("Sending data to host and port on public link:", host, port)
                s.connect((host, port))
                s.sendall(data_length + serialized_data)
            return True
        except (socket.error, Exception) as e:
            print("Error sending data:", e)
            return False

    @staticmethod
    def listen(port):
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
                    s.settimeout(1.0)
                    try:
                        conn, _ = s.accept()
                        with conn:
                            data = PublicChannel._receive_data(conn)
                            print("Data received on public channel", data)
                            if data and PublicChannel.message_handler:
                                PublicChannel.message_handler(data)
                    except socket.timeout:
                        continue

        PublicChannel.stop_event.clear()
        PublicChannel.listener_thread = threading.Thread(target=handler, daemon=True)
        PublicChannel.listener_thread.start()

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
        PublicChannel.stop_event.set()
        if PublicChannel.server_socket:
            PublicChannel.server_socket.close()
            PublicChannel.server_socket = None
        if PublicChannel.listener_thread:
            PublicChannel.listener_thread.join()
        print("Listener stopped.")
