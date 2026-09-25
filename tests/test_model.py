import json

import httpx
import pytest

from app.model import LocalModel, needs_subject

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


@pytest.mark.parametrize("question", ["When does it open?", "where do they start", "How much is it?", "How much does that cost?"])
async def test_context_dependent_question_requests_subject_without_model_call(question):
    model = LocalModel()
    await model.client.aclose()
    result = await model.answer(question, [SOURCE])
    assert result["reason"] == "clarification_needed"
    assert result["sources"] == []


@pytest.mark.parametrize("question", ["When does the laboratory open?", "When does it open according to the lab policy?", "How much does a badge cost?", "When does employee earn vacation?"])
def test_explicit_subject_questions_are_not_blocked(question):
    assert not needs_subject(question)


@pytest.mark.parametrize("question", ["What year was Northstar founded?", "When was this company established?", "What is its incorporation date?"])
async def test_document_date_is_not_company_origin_evidence(question):
    model = LocalModel()
    await model.client.aclose()
    result = await model.answer(question, [{"label": "S1", "text": "Handbook effective January 2026."}])
    assert result["reason"] == "missing_event_evidence"
    assert result["mode"] == "abstained"
