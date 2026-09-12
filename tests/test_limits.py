from app.limits import BodyLimitMiddleware


async def test_chunked_upload_limit_is_enforced_before_app():
    called = False
    async def app(scope, receive, send):
        nonlocal called
        called = True
    events = iter([{"type": "http.request", "body": b"123", "more_body": True},
                   {"type": "http.request", "body": b"456", "more_body": False}])
    sent = []
    async def receive():
        return next(events)
    async def send(event):
        sent.append(event)
    await BodyLimitMiddleware(app, 5)({"type": "http", "method": "POST",
                                     "path": "/api/documents"}, receive, send)
    assert not called
    assert sent[0]["status"] == 413
