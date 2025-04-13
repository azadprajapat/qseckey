from controllers.qkd.bb84.sender import Sender
from controllers.qkd.bb84.receiver import Receiver


class BB84KeyGenerator:
    _instances = {}

    def __new__(cls, key_id):
        if key_id not in cls._instances:
            instance = super().__new__(cls)
            instance._initialize(key_id)
            cls._instances[key_id] = instance
        return cls._instances[key_id]

    def _initialize(self, key_id):
        self.key_id = key_id
        self.sender = None
        self.receiver = None

    def init_sender(self, application_id, key_size, quantum_link_info, public_channel_info,completion_callback):
        if self.sender:
            return self.sender

        self.sender = Sender(self.key_id, application_id, key_size, quantum_link_info, public_channel_info,completion_callback)
        return self.sender

    def init_receiver(self, key_size, public_channel_info,completion_callback=None):
        if self.receiver:
            return self.receiver

        self.receiver = Receiver(self.key_id, key_size, public_channel_info,completion_callback)
        return self.receiver
    def handle_key_storage_receiver():
        pass
    def handle_key_storage_sender():
        pass

