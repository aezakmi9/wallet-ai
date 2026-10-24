import json
from confluent_kafka import Consumer
from app.config import KAFKA_SERVERS, KAFKA_GROUP_ID, INPUT_TOPIC
from app.detectors.rule_detector import detect_anomalies
from app.ai.explanation_service import explain

def run_consumer():
    consumer = Consumer({
        "bootstrap.servers": KAFKA_SERVERS,
        "group.id": KAFKA_GROUP_ID,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })

    # TODO: subscribe to wallet.* topics (e.g. regex '^wallet\\..*')
    consumer.subscribe([INPUT_TOPIC])

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                # TODO: don't kill the loop on every error — log and continue, retry transient ones
                raise RuntimeError(msg.error())

            # TODO: parse the platform envelope (eventId, eventType, schemaVersion, occurredAt, aggregateId, payload)
            # TODO: poison message (bad JSON / missing keys) should go to DLQ after N retries, not crash the consumer
            # TODO: dedup by eventId — delivery is at-least-once
            # TODO: propagate traceId from Kafka headers into logs
            event = json.loads(msg.value())
            # TODO: also run IsolationDetector (ML) here
            anomalies = detect_anomalies(event)

            if anomalies:
                # TODO: LLM failure/timeout must not crash the consumer — fall back to no explanation
                explanation = explain(event, anomalies)

                # TODO: publish to ai.transaction.flagged via anomaly_producer (key=userId) instead of print
                print({
                        "eventId": event["eventId"],
                        "anomalies": anomalies,
                        "explanation": explanation
                })

                # TODO: BUG — commit is inside `if anomalies`, so normal events are never committed
                #       and get reprocessed after restart. Move commit out of the if.
                consumer.commit(message=msg,asynchronous=False)
    finally:
        consumer.close()