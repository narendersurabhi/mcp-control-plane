from typing import Any

import pytest

pytest.importorskip("pytest_asyncio")
httpx = pytest.importorskip("httpx")


def _imports() -> tuple[Any, ...]:
    pytest.importorskip("pydantic")
    pytest.importorskip("mcp")
    from mcp_cp.adapters import default_audit_adapter, default_kb_adapter
    from mcp_cp.policy import ScopePolicy
    from mcp_cp.server import create_http_app, create_server

    return (
        default_audit_adapter,
        default_kb_adapter,
        ScopePolicy,
        create_http_app,
        create_server,
    )


@pytest.mark.asyncio  # type: ignore[misc]
async def test_http_auth_and_policy_allows_health_check() -> None:
    (
        default_audit_adapter,
        default_kb_adapter,
        ScopePolicy,
        create_http_app,
        create_server,
    ) = _imports()
    server = create_server(default_kb_adapter(), default_audit_adapter(), "1.0.0")
    app = create_http_app(server, token="token", policy=ScopePolicy())
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "health.check", "arguments": {}},
        }
        response = await client.post(
            "/",
            headers={"Authorization": "Bearer token", "X-MCP-Scope": "read"},
            json=payload,
        )
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["status"] == "ok"


@pytest.mark.asyncio  # type: ignore[misc]
async def test_http_auth_denied() -> None:
    (
        default_audit_adapter,
        default_kb_adapter,
        ScopePolicy,
        create_http_app,
        create_server,
    ) = _imports()
    server = create_server(default_kb_adapter(), default_audit_adapter(), "1.0.0")
    app = create_http_app(server, token="token", policy=ScopePolicy())
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "health.check", "arguments": {}},
        }
        response = await client.post("/", json=payload)
    assert response.status_code == 401
    body = response.json()
    assert body["error"]["message"] == "unauthorized"


@pytest.mark.asyncio  # type: ignore[misc]
async def test_http_policy_denied() -> None:
    (
        default_audit_adapter,
        default_kb_adapter,
        ScopePolicy,
        create_http_app,
        create_server,
    ) = _imports()
    server = create_server(default_kb_adapter(), default_audit_adapter(), "1.0.0")
    app = create_http_app(server, token="token", policy=ScopePolicy())
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "audit.query", "arguments": {"q": "foo"}},
        }
        response = await client.post(
            "/",
            headers={"Authorization": "Bearer token", "X-MCP-Scope": "read"},
            json=payload,
        )
    assert response.status_code == 403
    body = response.json()
    assert body["error"]["message"] == "forbidden"
