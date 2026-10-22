import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_SERVERS=os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID")
INPUT_TOPIC = os.getenv("KAFKA_INPUT_TOPIC")
OUTPUT_TOPIC = os.getenv("KAFKA_OUTPUT_TOPIC")

OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")