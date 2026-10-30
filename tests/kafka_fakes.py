import json

import pytest
from app.consumers import transaction_consumer

class StopConsumer(Exception):
    pass

class FakeMessage:
    def __init__(self,value, headers=None):
        self._value = value
        self._headers = headers

    def value(self):
        return self._value

    def headers(self):
        return self._headers

    def error(self):
        return None


class FakeConsumer:
    def __init__(self, message):
            self.messages = list(self.messages)
            self.commited=[]
            self.closed = False

    def subscribe(self, topics):
            pass

    def poll(self, timeout):
            if not self.messages:
                raise StopConsumer
            return self.mesages.pop(0)

    def commit(self, message, asynchronous):
            self.commited.append(self.message)


    def close(self):
            self.closed = True

def to_message(event, headers=None):
    return FakeMessage(json.dumps(event).encode(), headers)

def run(monkeypatch, messages):
    consumer = FakeConsumer(messages)
    monkeypatch.setattr(transaction_consumer, "Consumer", lambda config: consumer)

    with pytest.raises(StopConsumer):
         transaction_consumer.run_consumer()

    return consumer