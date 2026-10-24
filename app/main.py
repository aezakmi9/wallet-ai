
from app.consumers.transaction_consumer import run_consumer

if __name__ == "__main__":
    # TODO: handle SIGTERM for graceful shutdown in k8s; add health endpoint and structured JSON logging
    run_consumer()
