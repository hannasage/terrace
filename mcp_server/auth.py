"""
Authentication for the hosted Terrace MCP server.

A single shared secret, checked in constant time. When the server runs over HTTP
for a custom connector, every request must carry `Authorization: Bearer <token>`
matching TERRACE_MCP_TOKEN, or it is refused. That is the whole gate: the tools
are read-only over already-public Premier League facts, so the token exists to
keep Terrace from being an open service (operating principle 3), not to guard a
secret. Local stdio use (Claude Desktop and Code) runs without this, since the
transport is a private subprocess, not a network endpoint.

Full OAuth is available in the SDK if a connector flow ever requires it; a static
bearer token is the minimal verifier that satisfies the same interface.
"""

from __future__ import annotations

import hmac

from mcp.server.auth.provider import AccessToken, TokenVerifier


class StaticTokenVerifier(TokenVerifier):
    """Accepts exactly one bearer token, compared in constant time."""

    def __init__(self, secret: str) -> None:
        if not secret:
            raise ValueError(
                "TERRACE_MCP_TOKEN must be set to a non-empty secret when serving "
                "over HTTP."
            )
        self._secret = secret

    async def verify_token(self, token: str) -> AccessToken | None:
        # compare_digest avoids leaking the secret through timing.
        if hmac.compare_digest(token, self._secret):
            return AccessToken(
                token=token,
                client_id="terrace-owner",
                scopes=["terrace:read"],
            )
        return None
