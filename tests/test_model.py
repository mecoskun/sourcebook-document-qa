import json

import httpx
import pytest

from app.model import LocalModel

SOURCE = {"label": "S1", "text": "Employees get 20 vacation days.", "name": "policy.txt"}


@pytest.mark.parametrize("result,mode", [
    ({"supported": True, "statements": [{"text": "20 days.", "source_ids": ["S1"]}]}, "generated"),
    ({"supported": False, "statements": []}, "abstained"),
    ({"supported": True, "statements": [{"text": "20 days.", "source_ids": ["S99"]}]}, "extractive"),
    ({"supported": True, "statements": [{"text": "20 days.", "source_ids": []}]}, "extractive"),
    ({"supported": True, "statements": [{"text": "20 days. [S2]", "source_ids": ["S1"]}]}, "extractive"),
    ([], "extractive"),
    ({"supported": True, "statements": [{"text": "This policy is not specified.", "source_ids": ["S1"]}]}, "abstained"),
])
async def test_validates_model_citations(result, mode):
    model = LocalModel()
    await model.client.aclose()
    model.client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request:
        httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(result)}}]})))
    try:
        answer = await model.answer("Vacation?", [SOURCE])
        assert answer["mode"] == mode
    finally:
        await model.client.aclose()


async def test_no_evidence_never_calls_model():
    model = LocalModel()
    try:
        result = await model.answer("What is my salary?", [])
        assert result["mode"] == "abstained"
        assert result["sources"] == []
    finally:
        await model.client.aclose()
