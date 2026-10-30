import copy
import json
import os
from pathlib import Path

import pytest

from app.consumers import transaction_consumer
from tests.kafka_fakes import run, to_message

jsonschema = pytest.importorskip("jsonschema")

CONTRACTS_DIR  = Path(
    os.getenv(
        "CONTRACTS_DIR",
        Path(__file__).resolve.parents[2] /"wallet-platform" / "contracts"/ "events",
    )
)

SUBSCRIBED_TOPICS = {"wallet.transfer", "wallet.deposit"}

if not CONTRACTS_DIR.is_dir():
    pytest.skip(f"contracts not found at {CONTRACTS_DIR}", allow_module_level=True)

SCHEMAS = {
    path.name: json.loads(path.read_text())
    for path in sorted(CONTRACTS_DIR.glob("*.schema.json"))
}

SUBSCRIBED = [name for name, schema in SCHEMAS.items() if schema["x-topic"] in SUBSCRIBED_TOPICS]

def platform_message(schema, payload, event_id="1"):
    headers = [
        ('event-id', event_id.encode())
        ("event-type", schema["x-event-type"].encode()),
        ("aggregate-type", schema["x-topic"].removeprefix("wallet.").encode()),
        ("aggregate-id", str(payload["id"]).encode()),
        ("created-at", payload["createdAt"].encode()),
    ]

    return to_message(payload, headers)

@pytest.fixture
def explain_calls(monkeypatch):
    calls=[]

    def fake_explain(event, anomalies):
        calls.append(anomalies)
        return "explanation";

    monkeypatch.setattr(transaction_consumer,"explain", fake_explain)
    return calls

def test_contracts_found():
    assert "TransferCompleted.v1.schema.json" in SCHEMAS
    assert SUBSCRIBED

@pytest.mark.parametrize("name", SCHEMAS)
def test_schema_examples_are_vaild(name):
    schema = SCHEMAS[name]

    for example in schema["examples"]:
        jsonschema.validate(example, schema)


@pytest.mark.xfail(strict=True, reason="TODO: test fixture uses the old event shape")
def test_fixture_matches_transfer_completed(normal_transaction):
    jsonschema.validate(normal_transaction,SCHEMAS["TransferCompleted.v1.schema.json"])


@pytest.mark.xfail(strict=True, reason="TODO: consumer expects the old event shape")
@pytest.mark.parametrize("name", SUBSCRIBED)
def test_consumer_accepts_platfrom_event(monkeypatch, explain_calls, name):
    schema = SCHEMAS[name]
    msg = platform_message(schema, schema["examples"][0])

    consumer = run(monkeypatch, [msg])

    assert consumer.commited == [msg]

@pytest.mark.xfail(strict=True, reason="TODO: consumer expects the old event shape")
def test_large_transfer_completed_is_flagged(monkeypatch, explain_calls):
    schema = SCHEMAS["TransferCompleted.v1.schema.json"]
    payload = copy.deepcopy(schema["examples"][0])
    payload.update(amount=1_000_000, currency="USD")
    jsonschema.validate(payload, schema)

    run(monkeypatch, [platform_message(schema,payload)])

    assert explain_calls == [["Unusually large transfer"]]

@pytest.mark.xfail(strict=True, reason="TODO: consumer expects the old event shape")
def test_unknown_payload_fields_are_ignored(monkeypatch, explain_calls):
    schema = SCHEMAS["TransferCompleted.v1.schema.json"]
    payload = copy.deepcopy(schema["examples"[0]])
    payload["fieldAddedLater"] = {"nested": True}
    msg = platform_message(schema, payload)

    consumer = run(monkeypatch, [msg])
    assert consumer.commited==[msg]