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

    consumer.subscribe([INPUT_TOPIC])

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                raise RuntimeError(msg.error())

            event = json.loads(msg.value())
            anomalies = detect_anomalies(event)

            if anomalies:
                explanation = explain(event, anomalies)

                print({
                        "eventId": event["eventId"],
                        "anomalies": anomalies,
                        "explanation": explanation
                })

                consumer.commit(message=msg,asynchronous=False)
    finally:
        consumer.close()