import pytest

from app.ml.features import FEATURE_NAMES
from app.ml.isolation_detector import IsolationDetector


class FakeModel:

    def __init__(self,score):
        self.score = score

    def decision_function(self,X):
        assert len(X) ==1
        assert len(X[0]) == len(FEATURE_NAMES)
        return [self.score]


@pytest.mark.parametrize(
    "score,expected",
    [
        (-0.50, True),
        (-0.01, True),
        (0.00, False),
        (0.10, False),
        (0.80, False),
    ]
)
def test_anomaly_classification(
    monkeypatch,
    normal_transaction,
    score,
    expected,
):
    artifact = {
        "model": FakeModel(score),
        "feature_names": FEATURE_NAMES,
        "version": "v1",
    }

    monkeypatch.setattr(
        "app.ml.isolation_detector.joblib.load",
        lambda path: artifact,
    )


    detector = IsolationDetector("fake-model.joblib")

    result = detector.predict(normal_transaction)

    assert result["is_anomaly"] is expected
    assert result["score"] == pytest.approx(score)
    assert result["model_version"] =="v1"