# TODO: Kafka integration test (testcontainers) and contract tests against contracts/events/


import pytest

from app.detectors.rule_detector import detect_anomalies

LARGE_TRANSFER = "Unusually large transfer"

def test_normal_transfer_has_no_anomalies(normal_transaction):
    assert detect_anomalies(normal_transaction) ==[]


@pytest.mark.parametrize("amount",[500_000, 1_000_000])
def test_flags_large_usd_transfer(normal_transaction, amount):
    normal_transaction["amountMinor"] = amount

    assert detect_anomalies(normal_transaction) ==[LARGE_TRANSFER]


def test_amount_just_below_threshold_not_flagged(normal_transaction):
    normal_transaction["amountMinor"] = 499_999

    assert detect_anomalies(normal_transaction) ==[]


@pytest.mark.parametrize("event_type", ["DEPOSIT_COMPLETED", "TRANSFER_FAILED",""])
def test_non_transfer_events_ignored(normal_transaction, event_type):
    normal_transaction["eventType"] = event_type
    normal_transaction["amountMinor"] = 1_000_000
    normal_transaction["balanceAfterMinor"] = -100

    assert detect_anomalies(normal_transaction) ==[]


@pytest.mark.parametrize("currency", ["EUR", "VND"])
def test_other_currencies_not_flagged(normal_transaction,currency):
    normal_transaction["currency"] = currency
    normal_transaction["amountMinor"] = 1_000_000

    assert detect_anomalies(normal_transaction) ==[]
