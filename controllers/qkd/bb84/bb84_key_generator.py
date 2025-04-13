from controllers.qkd.bb84.sender import Sender
from controllers.qkd.bb84.receiver import Receiver

class BB84KeyGenerator:
    _instances = {}

    def __new__(cls, key_id,completion_callback_sender=None):
        if key_id not in cls._instances:
            instance = super().__new__(cls)
            instance._initialize(key_id,completion_callback_sender)
            cls._instances[key_id] = instance
        return cls._instances[key_id]

    def _initialize(self, key_id,completion_callback_sender=None):
        self.key_id = key_id
        self.sender = None
        self.receiver = None
        self.completion_callback_sender = completion_callback_sender

    def init_sender(self, application_id, key_size, quantum_link_info, public_channel_info):
        if self.sender:
            return self.sender

        self.sender = Sender(self.key_id, application_id, key_size, quantum_link_info, public_channel_info,self.completion_callback_sender)
        return self.sender
    def init_receiver(self, key_size, public_channel_info,completion_callback=None):
        if self.receiver:
            return self.receiver

        self.receiver = Receiver(self.key_id, key_size, public_channel_info,completion_callback)
        return self.receiver

    def init_key_generation(self,connection_info):
        quantum_link_info = {
            "target": connection_info.get('target_KME_ID'),
            "source": connection_info.get('source_KME_ID')
        }

        public_channel_info = {
            "target": connection_info.get('target_KME_ID'),
            "source": connection_info.get('source_KME_ID')
        }
        self.sender = self.init_sender(
            connection_info.get('application_id'),
            connection_info.get('key_size'),
            quantum_link_info,
            public_channel_info
        )
        self.sender.run_protocol()
