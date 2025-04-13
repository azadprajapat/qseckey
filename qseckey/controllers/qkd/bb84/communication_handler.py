from qseckey.controllers.qkd.bb84.bb84_key_generator import BB84KeyGenerator
class BB84CommunicationHandler:
    def __init__(self, completion_callback):
        self.completion_callback = completion_callback
    def handle_quantum_channel_data(self,data):
        if data.get('event') == 'TEST':
            print("[Quantum Channel] Test event received")
            return

        if data.get('source_type') != "SENDER":
            print("[Quantum Channel] Invalid source type")
            return

        generator = BB84KeyGenerator(data['key_id'])
        receiver = generator.init_receiver(key_size="", public_channel_info="",completion_callback=None)  # Adjust if needed
        receiver.listener(data)


    def handle_public_channel_data(self,data):
        generator = BB84KeyGenerator(data['key_id'])
        source_type = data.get('source_type')

        if source_type == "RECEIVER":
            sender = generator.init_sender(
                application_id=data.get('application_id'),
                key_size=data.get('key_size'),
                quantum_link_info=data.get('quantum_link_info'),
                public_channel_info=data.get('public_channel_info')
            )
            sender.listener(data)
        else:
            receiver = generator.init_receiver(
                data.get('key_size'),
                data.get('source_host'),
                self.completion_callback
            )
            receiver.listener(data)
