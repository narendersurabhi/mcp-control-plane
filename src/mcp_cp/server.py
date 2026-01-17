from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from mcp.server import Server
from mcp.server.http import StreamableHTTPServer
from mcp.server.stdio import stdio_server
from prometheus_client import start_http_server

from mcp_cp.adapters import (
    AuditAdapter,
    KBAdapter,
    default_audit_adapter,
    default_kb_adapter,
)
from mcp_cp.logging import configure_logging, get_logger
from mcp_cp.models import (
    AuditQueryInput,
    AuditQueryResponse,
    DocumentResource,
    ErrorResponse,
    HealthCheckResponse,
    KBSearchInput,
    KBSearchResponse,
)
from mcp_cp.policy import ScopePolicy
from mcp_cp.telemetry import configure_tracing, request_span

ASGIApp = Callable[[dict[str, Any], "Receive", "Send"], Awaitable[None]]
Receive = Callable[[], Awaitable[dict[str, Any]]]
Send = Callable[[dict[str, Any]], Awaitable[None]]


@dataclass
class RequestContext:
    request_id: str


def _request_id_from_context(context: Any | None) -> str:
    if context is None:
        return str(uuid4())
    return getattr(context, "request_id", str(uuid4()))


def handle_health_check(version: str, context: RequestContext | None = None) -> HealthCheckResponse:
    request_id = _request_id_from_context(context)
    logger = get_logger(request_id, "health.check")
    with request_span("tool", "health.check"):
        logger.info("health_check")
        return HealthCheckResponse(
            status="ok",
            deps={"kb": "ok", "audit": "ok"},
            version=version,
        )


def handle_kb_search(
    adapter: KBAdapter, input_data: KBSearchInput, context: RequestContext | None = None
) -> KBSearchResponse:
    request_id = _request_id_from_context(context)
    logger = get_logger(request_id, "kb.search")
    with request_span("tool", "kb.search"):
        logger.info("kb_search")
        return adapter.search(input_data.query, input_data.top_k)


def handle_audit_query(
    adapter: AuditAdapter,
    input_data: AuditQueryInput,
    context: RequestContext | None = None,
) -> AuditQueryResponse:
    request_id = _request_id_from_context(context)
    logger = get_logger(request_id, "audit.query")
    with request_span("tool", "audit.query"):
        logger.info("audit_query")
        return adapter.query(input_data.q, input_data.limit)


def handle_kb_resource(
    adapter: KBAdapter, doc_id: str, context: RequestContext | None = None
) -> DocumentResource:
    request_id = _request_id_from_context(context)
    logger = get_logger(request_id, "kb.resource")
    with request_span("resource", "kb.resource"):
        logger.info("kb_resource")
        return adapter.get_document(doc_id)


def create_server(kb_adapter: KBAdapter, audit_adapter: AuditAdapter, version: str) -> Server:
    server = Server("mcp-control-plane")

    @server.tool("health.check")  
    async def health_check() -> dict[str, Any]:
        return handle_health_check(version).model_dump()  # type: ignore[no-any-return]

    @server.tool("kb.search")  # type: ignore[misc]
    async def kb_search(query: str, top_k: int = 5) -> dict[str, Any]:
        result = handle_kb_search(kb_adapter, KBSearchInput(query=query, top_k=top_k))
        return result.model_dump()  # type: ignore[no-any-return]

    @server.tool("audit.query")  # type: ignore[misc]
    async def audit_query(q: str, limit: int = 50) -> dict[str, Any]:
        result = handle_audit_query(audit_adapter, AuditQueryInput(q=q, limit=limit))
        return result.model_dump()  # type: ignore[no-any-return]

    @server.resource("kb://documents/{doc_id}")  
    async def kb_document(doc_id: str) -> dict[str, Any]:
        result = handle_kb_resource(kb_adapter, doc_id)
        return result.model_dump()  # type: ignore[no-any-return]

    @server.prompt("incident_triage")  
    async def incident_triage() -> str:
        return (
            "You are an incident triage assistant. First call health.check. "
            "Then call kb.search with the incident summary to gather relevant context."
        )

    return server


class AuthPolicyMiddleware:
    def __init__(self, app: ASGIApp, token: str, policy: ScopePolicy) -> None:
        self.app = app
        self.token = token
        self.policy = policy

    async def __call__(self, scope: dict[str, Any], receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        body = await _read_body(receive)
        request = json.loads(body.decode("utf-8")) if body else {}
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        headers = {k.decode("latin-1"): v.decode("latin-1") for k, v in scope.get("headers", [])}
        auth_header = headers.get("authorization", "")
        scope_header = headers.get("x-mcp-scope", "")
        if not self._authorized(auth_header):
            await _send_jsonrpc_error(
                send,
                request_id,
                401,
                "unauthorized",
                {"detail": "missing or invalid bearer token"},
            )
            return

        action = _action_from_request(method, params)
        if action:
            decision = self.policy.allows(scope_header or "", action)
            if not decision.allowed:
                await _send_jsonrpc_error(
                    send,
                    request_id,
                    403,
                    "forbidden",
                    {"detail": decision.reason},
                )
                return
        else:
            await _send_jsonrpc_error(
                send,
                request_id,
                403,
                "forbidden",
                {"detail": "action not allowed"},
            )
            return

        async def buffered_receive() -> dict[str, Any]:
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, buffered_receive, send)

    def _authorized(self, auth_header: str) -> bool:
        if not self.token:
            return False
        return auth_header == f"Bearer {self.token}"


async def _read_body(receive: Receive) -> bytes:
    chunks: list[bytes] = []
    more_body = True
    while more_body:
        message = await receive()
        chunks.append(message.get("body", b""))
        more_body = message.get("more_body", False)
    return b"".join(chunks)


def _action_from_request(method: str | None, params: dict[str, Any]) -> str | None:
    if method == "tools/call":
        return params.get("name")
    if method == "resources/read":
        return "kb.resource"
    return None


async def _send_jsonrpc_error(
    send: Send, request_id: Any, code: int, message: str, data: dict[str, Any]
) -> None:
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": ErrorResponse(code=code, message=message, data=data).model_dump(),
    }
    body = json.dumps(payload).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": code,
            "headers": [(b"content-type", b"application/json")],
        }
    )
    await send({"type": "http.response.body", "body": body})


def create_http_app(server: Server, token: str, policy: ScopePolicy) -> ASGIApp:
    http_server = StreamableHTTPServer(server)
    return AuthPolicyMiddleware(http_server.app, token=token, policy=policy)


async def run_stdio(server: Server) -> None:
    async with stdio_server() as (read, write):
        init_options: Any = {}
        await server.run(read, write, initialization_options=init_options)


async def run_http(server: Server) -> None:
    token = os.getenv("MCP_BEARER_TOKEN", "")
    policy = ScopePolicy()
    app = create_http_app(server, token=token, policy=policy)
    http_server = StreamableHTTPServer(server, app=app)
    await http_server.serve(host="0.0.0.0", port=int(os.getenv("MCP_HTTP_PORT", "8080")))


def main() -> None:
    configure_logging()
    configure_tracing()
    start_http_server(int(os.getenv("MCP_METRICS_PORT", "8001")))
    version = os.getenv("MCP_VERSION", "0.1.0")
    kb_adapter = default_kb_adapter()
    audit_adapter = default_audit_adapter()
    server = create_server(kb_adapter, audit_adapter, version)
    mode = os.getenv("MCP_MODE", "stdio")
    if mode == "http":
        asyncio.run(run_http(server))
    else:
        asyncio.run(run_stdio(server))


if __name__ == "__main__":
    main()
