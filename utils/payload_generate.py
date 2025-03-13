class PayloadGenerator:
    @staticmethod
    def protocol_begin(source_type, source_host, key_size, connection_id, event, key_id):
        return {
            "source_type": source_type,
            "source_host": source_host,
            "key_id": key_id,
            "event": event,
            "connection_id": connection_id,
            "key_size": key_size,
        }

    @staticmethod
    def send_bases(source_type, key_id, event, bases):
        return {
            "source_type": source_type,
            "key_id": key_id,
            "event": event,
            "bases": bases,
        }

    @staticmethod
    def send_qubits(source_type, source_host, key_id, event, rho):
        return {
            "source_type": source_type,
            "source_host": source_host,
            "key_id": key_id,
            "event": event,
            "qubits": rho,
        }
