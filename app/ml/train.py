from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.ml.features import extract_features, FEATURE_NAMES


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "app" / "data" / "transactions.csv"
MODEL_PATH = PROJECT_ROOT / "artifacts" / "isolation_forest.joblib"


def train():
    # TODO: only ~20 training rows — generate synthetic data or document it as a demo in README
    df = pd.read_csv(DATA_PATH)


    X = [
        extract_features(row)
        for row in df.to_dict("records")
    ]

    model = IsolationForest(
        n_estimators=200,
        max_samples="auto",
        contamination=0.15,  # ~3 of 20 training rows are outliers
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X)

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    joblib.dump({
        "model": model,
        "feature_names": FEATURE_NAMES,
        "version": "v1"
    }, MODEL_PATH)

    print(f"Trained using {len(X)} transactions")
    print(f"Saved model: {MODEL_PATH}")


if __name__ == "__main__":
    train()
