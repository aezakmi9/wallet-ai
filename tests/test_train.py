import joblib
import pandas as pd
from importlib import import_module
import pytest

from app.ml.isolation_detector import IsolationDetector
from app.ml.features import FEATURE_NAMES


train_module = import_module("app.ml.train")

def make_transactions(n=300):
      return [
            {
                 "currency": "USD",
                             "amountMinor": 2000 + (i % 30) * 100,
                             "avgTransferMinor30d": 3500,
                             "previousTransfers1h": i % 4, 
            }
            for i in range(n)
      ]

def run_train(tmp_dir, transactions):
      tmp_dir.mkdir(parents=True, exist_ok=True)
      data_path = tmp_dir / "transactions.csv"
      model_path = tmp_dir / "model.joblib"
      pd.DataFrame(transactions).to_csv(data_path,index=False);

      with pytest.MonkeyPatch.context() as mp:
            mp.setattr(train_module,"DATA_PATH", data_path)
            mp.setattr(train_module, "MODEL_PATH",model_path)
            train_module.train()
      return model_path;

@pytest.fixture(scope="module")
def model_path(tmp_path_factory):
      return run_train(tmp_path_factory.mktemp("model"), make_transactions())

@pytest.fixture(scope="module")
def detector(model_path):
      return IsolationDetector(str(model_path))

@pytest.fixture
def normal_event():
      return {
        "currency": "USD",
        "amountMinor": 3000,
        "avgTransferMinor30d": 3500,
        "previousTransfers1h": 2,
      }

@pytest.fixture
def unusual_event():
      return {
        "currency": "USD",
        "amountMinor": 900_000,
        "avgTransferMinor30d": 3500,
        "previousTransfers1h": 45,  
      }

def test_train_saves_artifact(model_path):
      assert model_path.exists()

      artifact = joblib.load(model_path)

      assert artifact["feature_names"] == FEATURE_NAMES
      assert artifact["version"] =="v1"

def test_train_reports_row_count(tmp_path, capsys):
      run_train(tmp_path, make_transactions(50))

      assert "Trained using 50 transactions" in capsys.readouterr().out


def test_normal_events_is_not_anomaly(detector, normal_event):
      result = detector.predict(normal_event)

      assert result["is_anomaly"] is False
      assert result["model_version"] =="v1"

def test_unusual_event_is_anomaly(detector, unusual_event):
    result = detector.predict(unusual_event)

    assert result["is_anomaly"] is True
    assert result["model_version"] == "v1"

def test_unusual_scores_lower_than_normal(detector, normal_event, unusual_event):
      assert detector.predict(unusual_event)["score"] < detector.predict(normal_event)["score"]

def test_training_is_deterministic(tmp_path, normal_event):
      transactions = make_transactions()
      first = IsolationDetector(str(run_train(tmp_path / "a", transactions)))
      second = IsolationDetector(str(run_train(tmp_path / "b", transactions)))

      assert first.predict(normal_event)["score"] == second.predict(normal_event)["score"]

def test_flags_roughly_contamination_share_of_training_rows(detector):
      transactions = make_transactions()
      flagged = sum(detector.predict(t)["is_anomaly"] for t in transactions)

      assert flagged / len(transactions) = pytest.approx(0.15, abs=0.05)


@pytest.mark.parametrize(
      "bad_row",
      [
                    {"currency": "EUR", "amountMinor": 3000, "avgTransferMinor30d": 3500, "previousTransfers1h": 1},
        {"currency": "USD", "amountMinor": 0, "avgTransferMinor30d": 3500, "previousTransfers1h": 1},
        {"currency": "USD", "amountMinor": 3000, "avgTransferMinor30d": 3500, "previousTransfers1h": -1},
      ],

      ids = ["non-usd", "zero-amount", "negative-count"]
)
def test_train_fails_on_invalid_row(tmp_path, bad_row):
      with pytest.raises(ValueError):
            run_train(tmp_path,make_transactions(20) + [bad_row])


def test_train_fails_on_empty_csv(tmp_path):
      (tmp_path / "transactions.csv").write_text("currency,amountMinor,avgTransferMinor30d,previousTransfers1h\n")

      with pytest.MonkeyPatch.context() as mp:
            mp.setattr(train_module, "DATA_PATH", tmp_path / "transactions.csv")
            mp.setattr(train_module, "MODEL_PATH", tmp_path / "model.joblib")
            with pytest.raises(ValueError):
                train_module.train()

