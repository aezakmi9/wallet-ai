import json
import httpx

import pytest

from app.consumers import transaction_consumer


class StopConsumer(Exception):
    pass

class FakeMessage:
    def __init__(self,value):
        self._value=value

    def value(self):
        return self._value

    def error(self):
        return None

class FakeConsumer:
    def __init__(self, messages):
        self.messages = list(messages)
        self.commited = []
        self.closed = False

    def subscribe(self, topics):
        pass

    def poll(self,timeout):
        if not self.messages:
            raise StopConsumer
        return self.messages.pop(0)

    def commit(self, message, asynchronous):
        self.commited.append(message)

    def close(self):
        self.closed = True

def to_message(event):
    return FakeMessage(json.dumps(event).encode())


@pytest.fixture
def large_transaction(normal_transaction):
    normal_transaction["amountMinor"] = 1_000_000
    return normal_transaction


@pytest.fixture
def explain_calls(monkeypatch):
    calls=[]

    def fake_explain(event, anomalies):
        calls.append(event["evenId"])
        return "explanation"


    monkeypatch.setattr(transaction_consumer,"explain", fake_explain)
    return calls


def run(monkeypatch, messages):
    consumer = FakeConsumer(messages)
    monkeypatch.setattr(transaction_consumer,"Consumer", lambda config: consumer)

    with pytest.raises(StopConsumer):
        transaction_consumer.run_consumer()

    return consumer

def test_flagged_event_is_explained_and_commited(monkeypatch, large_transaction,explain_calls):
    msg = to_message(large_transaction)

    consumer = run(monkeypatch,[msg])

    assert explain_calls ==["event-001"]
    assert consumer.commited ==[msg]
    assert consumer.closed


@pytest.mark.xfail(strict=True, reason = "BUG: commit is inside `if anomalies`")
def test_normal_events_is_commited(monkeypatch, normal_transaction, explain_calls):
    msg = to_message(normal_transaction)

    consumer  =run(monkeypatch,[msg])

    assert explain_calls ==[]
    assert consumer.commited ==[msg]


@pytest.mark.xfail(strict=True, reason="TODO: dedup by eventId not implemented")
def test_duplicate_event_id_processed_once(monkeypatch, large_transaction, explain_calls):
    first = to_message(large_transaction)
    duplicate = to_message(large_transaction)


    consumer = run(monkeypatch, [first, duplicate])

    assert explain_calls ==["event-001"]
    assert consumer.commited == [first,duplicate]


# TODO: assert the message was published to the DLQ once that producer exists
@pytest.mark.xfail(strict=True, reason="TODO: poison messages crash the consumer")
@pytest.mark.parametrize("payload", [b"not json", b'{"eventId": "event-002"}'])
def test_poison_message_does_not_stop_consumer(monkeypatch, large_transaction,explain_calls, payload):
    poison = FakeMessage(payload)
    valid = to_message(large_transaction)

    consumer = run(monkeypatch, [poison, valid])

    assert explain_calls ==["event-001"]
    assert consumer.commited ==[poison, valid]

@pytest.mark.xfail(strict=True, reason="TODO: LLM failure crashes the consumer")
def test_ollama_down_does_not_stop_consumer(monkeypatch, large_transaction):
    def failing_explain(event, anomalies):
        raise httpx.ConnectError("Ollama is down")

    monkeypatch.setattr(transaction_consumer,"explain", failing_explain)
    msg = to_message(large_transaction)

    consumer = run(monkeypatch, [msg])

    assert consumer.commited ==[msg]








