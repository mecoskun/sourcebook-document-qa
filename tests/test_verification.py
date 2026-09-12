import json

import httpx

from app.model import LocalModel


async def test_evidence_check_can_reject_formatted_but_unsupported_answer():
    model = LocalModel()
    await model.client.aclose()
    calls = 0
    def respond(request):
        nonlocal calls
        calls += 1
        content = ({"supported": True, "statements": [{"text": "France won.", "source_ids": ["S1"]}]}
                   if calls == 1 else {"supported": False})
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(content)}}]})
    model.client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    try:
        answer = await model.answer("Who won?", [{"label": "S1", "text": "Leave is 20 days."}])
        assert answer["mode"] == "abstained"
        assert answer["sources"] == []
        assert calls == 2
    finally:
        await model.client.aclose()
