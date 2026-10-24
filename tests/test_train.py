import joblib
import pandas as pd
from importlib import import_module

from app.ml.isolation_detector import IsolationDetector
from app.ml.features import FEATURE_NAMES


train_module = import_module("app.ml.train")

def test_train_and_predict(tmp_path,monkeypatch):
    transactions=[]

    for i in range(300):
            transactions.append({
            "currency": "USD",
            "amountMinor": 2000 + (i % 30) * 100,
            "avgTransferMinor30d": 3500,
            "previousTransfers1h": i % 4,
        })
    data_path = tmp_path / "transactions.csv"
    model_path = tmp_path / "model.joblib"

    pd.DataFrame(transactions).to_csv(
          data_path, index = False
    )

    monkeypatch.setattr(
          train_module,"DATA_PATH", data_path
    )
    monkeypatch.setattr(
          train_module, "MODEL_PATH", model_path
    )

    train_module.train()

    assert model_path.exists()

    artifact = joblib.load(model_path)

    assert artifact["feature_names"] == FEATURE_NAMES
    assert artifact["version"] == "v1"


    detector = IsolationDetector(str(model_path))

    normal = {
        "currency": "USD",
        "amountMinor": 3000,
        "avgTransferMinor30d": 3500,
        "previousTransfers1h": 2,
    }

    unusual = {
        "currency": "USD",
        "amountMinor": 900000,
        "avgTransferMinor30d": 3500,
        "previousTransfers1h": 45,
    }

    normal_result = detector.predict(normal)
    unusual_result = detector.predict(unusual)

    assert unusual_result["score"] < normal_result["score"]

