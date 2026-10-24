from unittest.mock import Mock

from app.ai.explanation_service import explain

def test_explanation_generation(
          monkeypatch,
    normal_transaction,  
):
    response = Mock()

    response.json.return_value = {
                "response": (
            "This transfer is unusual because "
            "of its amount and frequency."
        )
    }

    def fake_post(url,json,timeout):
        assert url.endswith("/api/generate")
        assert json["stream"] is False
        assert "model" in json
        assert "prompt" in json

        return response

    monkeypatch.setattr(
        "app.ai.explanation_service.httpx.post",
        fake_post,
    )

    result = explain(
        normal_transaction,
        ["High transaction amount"],
    )

    assert "unusual" in result.lower()
    response.raise_for_status.assert_called_once()