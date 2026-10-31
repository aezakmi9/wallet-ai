import json
import logging

from confluent_kafka import Producer

from app.config import KAFKA_SERVERS, OUTPUT_TOPIC

logger = logging.getLogger(__name__)


class AnomalyProducer:

    def __init__(self):
        self.producer= Producer({
            'bootstrap.servers':KAFKA_SERVERS,
            "enable.idempotence":True,
            "acks":"all",
        })

    def publish(self, key: str, result: dict) -> None:
        self.producer.produce(
            OUTPUT_TOPIC,
            key=key.encode("utf-8"),
            value=json.dumps(result).encode("utf-8"),
            on_delivery=self._on_delivery,
        )
        self.producer.poll(0)

    def flush(self, timeout: float = 10.0) -> None:
        remaining = self.producer.flush(timeout)
        if remaining:
            raise RuntimeError(f"{remaining} flagged events not delivered");

    @staticmethod
    def _on_delivery(err,msg):
        if err is not None:
            logger.error("Delivery to %s failed: %s", msg.topic(), err)