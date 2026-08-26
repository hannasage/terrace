"""
API-key authentication for the hosted Terrace MCP server.

A pure-ASGI middleware that requires a shared secret on every HTTP request, in a
familiar API-key shape: `Authorization: Bearer <key>` or `X-API-Key: <key>`,
matched in constant time against TERRACE_API_KEY. A request without a valid key
gets a plain 401.

It is pure ASGI on purpose. Starlette's BaseHTTPMiddleware buffers the response
body, which breaks the server-sent-event streaming the MCP transport uses; a
plain ASGI wrapper passes the stream through untouched.

The 401 carries no WWW-Authenticate OAuth challenge, so Claude's connector does
not fall into an OAuth flow: the server stays a plain endpoint that expects a
credential header, which is what the connector's request-headers field supplies.
See docs/DECISIONS.md D-016.
"""

from __future__ import annotations

import hmac


class ApiKeyMiddleware:
    """Reject any HTTP request that does not carry the shared API key."""

    def __init__(self, app, api_key: str) -> None:
        if not api_key:
            raise ValueError("TERRACE_API_KEY must be a non-empty secret.")
        self.app = app
        self.api_key = api_key

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            # Lifespan and any non-HTTP scope pass straight through.
            await self.app(scope, receive, send)
            return
        if self._authorized(scope):
            await self.app(scope, receive, send)
            return
        await self._reject(send)

    def _authorized(self, scope) -> bool:
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        presented: str | None = None

        authorization = headers.get(b"authorization")
        if authorization:
            text = authorization.decode("latin-1")
            if text[:7].lower() == "bearer ":
                presented = text[7:].strip()

        if presented is None:
            api_key_header = headers.get(b"x-api-key")
            if api_key_header:
                presented = api_key_header.decode("latin-1").strip()

        return presented is not None and hmac.compare_digest(presented, self.api_key)

    async def _reject(self, send) -> None:
        body = b'{"error": "unauthorized"}'
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
