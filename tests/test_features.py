import math
import pytest

from app.ml.features import extract_features


def test_extract_features(normal_transaction):
    result = extract_features(normal_transaction)

    assert len(result)==3

    assert result[0] == pytest.approx(math.log1p(150))

    assert result[1] ==2.0

    assert result[2] ==pytest.approx(5.0)


@pytest.mark.parametrize(
    "field,value",
    [
        ("amountMinor", 0),
        ("amountMinor", -100),
        ("avgTransferMinor30d", 0),
        ("previousTransfers1h", -1),
    ]
)
def test_reject_invalid_values(
    normal_transaction,field,value):
    normal_transaction[field] = value

    with pytest.raises(ValueError):
        extract_features(normal_transaction)


def test_reject_unsupported_currency(normal_transaction):
    normal_transaction["currency"] = "EUR"

    with pytest.raises(ValueError):
        extract_features(normal_transaction)