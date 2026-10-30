import json
import time
import uuid

import pytest


from confluent_kafka import Consumer, Producer, TopicPartition

from app.consumers import transaction_consumer

kafka = pytest.importorskip("testcontainers.community.kafka")

pytestmark = pytest.mark.integration


class StopConsumer(Exception):
    pass

class StoppingConsumer:
    """Real consumer that stops the loop after the first commit or a timeout."""

    def __init__(self, config, timeout=30):
        self._consumer = Consumer(config)
        self._deadline = time.monotonic() + timeout
        self.commited = False

    def poll(self, timeout):
        if self.commited:
            raise StopConsumer
        if time.monotonic() > self._deadline:
            raise TimeoutError("consumer did not commit in time")
        return self._consumer.poll(timeout)

    def commit(self, **kwargs):
        self._consumer.commit(**kwargs)
        self.commited= True

    def __getattr__(self, name):
        return getattr(self._consumer,name)

@pytest.fixture(scope="module")
def bootstrap_servers():
    try:
        container = kafka.KafkaContainer().with_kraft().start()
    except Exception as exc:
        pytest.skip(f"Kafka container unavailable: {exc}")

    yield container.get_bootstrap_server()
    container.stop()

@pytest.fixture
def topic(monkeypatch, bootstrap_servers):
    name = f"wallet.transfer.{uuid.uuid4().hex[:8]}"
    group_id = f"wallet-ai-{uuid.uuid4().hex[:8]}"

    monkeypatch.setattr(transaction_consumer, "KAFKA_SERVERS", bootstrap_servers)
    monkeypatch.setattr(transaction_consumer, "KAFKA_GROUP_ID", group_id)
    monkeypatch.setattr(transaction_consumer, "INPUT_TOPIC", name)
    monkeypatch.setattr(transaction_consumer, "Consumer", StoppingConsumer)

    return name


@pytest.fixture
def explain_calls(monkeypatch):
    calls=[]

    def fake_explain(event, anomalies):
        calls.append(event["eventId"])
        return "explanation"

    monkeypatch.setattr(transaction_consumer, "explain",fake_explain)
    return calls

def publish(bootstrap_servers, topic, event):
    producer = Producer({"bootstrap.servers": bootstrap_servers})
    producer.produce(topic, key=event["accountId"], value=json.dump(event))
    assert producer.flush(10) ==0;

def commited_offset(bootstrap_servers, topic):
    consumer = Consumer({
        "bootstrap.servers": bootstrap_servers,
        "group.id": transaction_consumer.KAFKA_GROUP_ID,
    })

    try:
        [partition] = consumer.committed([TopicPartition(topic,0)], timeout=10)
        return partition.offset
    finally:
        consumer.close


def test_flagged_event_is_consumed_and_commited(bootstrap_servers, topic, explain_calls, normal_transaction):
    normal_transaction["amountMinor"] = 1_000_000
    publish(bootstrap_servers, topic, normal_transaction)

    with pytest.raises(StopConsumer):
        transaction_consumer.run_consumer()

    assert explain_calls ==["event-001"]
    assert commited_offset(bootstrap_servers, topic)==1


@pytest.mark.xfail(strict=True, raises=TimeoutError, reason="BUG: commit is inside `if anomalies`")
def test_normal_event_is_commited(bootstrap_servers, topic, explain_calls, normal_transaction):

    with pytest.raises(StopConsumer):
        transaction_consumer.run_consumer()

    assert commited_offset(bootstrap_servers, topic)==1
