import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_SERVERS=os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID")
# TODO: subscribe to all wallet.* topics (wallet.transfer, wallet.deposit), not a single input topic
INPUT_TOPIC = os.getenv("KAFKA_INPUT_TOPIC")
# TODO: actually publish results here (ai.transaction.flagged) — currently unused
OUTPUT_TOPIC = os.getenv("KAFKA_OUTPUT_TOPIC")

OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

# TODO: read ANOMALY_THRESHOLD_MINOR from .env and use it in rule_detector (per currency)