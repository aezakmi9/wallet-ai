import pytest

@pytest.fixture
def normal_transaction():
    return {
        "eventId": "event-001",
        "eventType": "TRANSFER_COMPLETED",
        "accountId": "account-123",
        "currency": "USD",
        "amountMinor": 15000,
        "avgTransferMinor30d": 3000,
        "previousTransfers1h": 2,
        "balanceAfterMinor": 50000,
    }