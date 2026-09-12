from starlette.responses import JSONResponse


class BodyLimitMiddleware:
    """Enforce an actual streaming byte cap before multipart parsing, including chunked bodies."""
    def __init__(self, app, limit: int):
        self.app = app
        self.limit = limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            return await self.app(scope, receive, send)
        limit = self.limit if scope["path"] == "/api/documents" else 8192
        parts = []
        size = 0
        while True:
            event = await receive()
            if event["type"] == "http.disconnect":
                return
            body = event.get("body", b"")
            size += len(body)
            if size > limit:
                response = JSONResponse({"detail": "Request exceeds the upload or text limit."}, 413)
                return await response(scope, receive, send)
            parts.append(body)
            if not event.get("more_body", False):
                break
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": b"".join(parts), "more_body": False}
            return await receive()

        await self.app(scope, bounded_receive, send)
