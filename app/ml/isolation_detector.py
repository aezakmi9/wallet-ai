import joblib

from app.ml.features import (
    FEATURE_NAMES,
    extract_features,
)


class IsolationDetector:

    def __init__(self, model_path: str):
        artifact = joblib.load(model_path)

        if artifact["feature_names"] !=FEATURE_NAMES:
            raise ValueError("Schema mismatch")

        self.model = artifact["model"]
        self.version = artifact["version"]

    def predict(self, event: dict) -> dict:
        features = extract_features(event)


        X = [features]

        score = float(
            self.model.decision_function(X)[0]
        )

        return{
            "is_anomaly": score < 0,
            "score": score,
            "model_version": self.version,
        }