import pytest


def _imports() -> tuple[object, ...]:
    pytest.importorskip("pydantic")
    pytest.importorskip("mcp")
    from mcp_cp.adapters import InMemoryAuditAdapter, InMemoryKBAdapter
    from mcp_cp.models import AuditQueryInput, DocumentMetadata, DocumentResource, KBSearchInput
    from mcp_cp.server import (
        RequestContext,
        handle_audit_query,
        handle_health_check,
        handle_kb_resource,
        handle_kb_search,
    )

    return (
        InMemoryAuditAdapter,
        InMemoryKBAdapter,
        AuditQueryInput,
        DocumentMetadata,
        DocumentResource,
        KBSearchInput,
        RequestContext,
        handle_audit_query,
        handle_health_check,
        handle_kb_resource,
        handle_kb_search,
    )


def test_health_check() -> None:
    (
        _InMemoryAuditAdapter,
        _InMemoryKBAdapter,
        _AuditQueryInput,
        _DocumentMetadata,
        _DocumentResource,
        _KBSearchInput,
        RequestContext,
        _handle_audit_query,
        handle_health_check,
        _handle_kb_resource,
        _handle_kb_search,
    ) = _imports()
    response = handle_health_check("1.2.3", RequestContext(request_id="req-1"))
    assert response.status == "ok"
    assert response.version == "1.2.3"


def test_kb_search() -> None:
    (
        _InMemoryAuditAdapter,
        InMemoryKBAdapter,
        _AuditQueryInput,
        DocumentMetadata,
        DocumentResource,
        KBSearchInput,
        _RequestContext,
        _handle_audit_query,
        _handle_health_check,
        _handle_kb_resource,
        handle_kb_search,
    ) = _imports()
    adapter = InMemoryKBAdapter(
        documents={
            "doc": DocumentResource(
                metadata=DocumentMetadata(id="doc", title="Runbook", tags=["ops"]),
                content="Use the runbook for incidents.",
            )
        }
    )
    response = handle_kb_search(adapter, KBSearchInput(query="runbook", top_k=5))
    assert response.results
    assert response.results[0].id == "doc"


def test_kb_resource() -> None:
    (
        _InMemoryAuditAdapter,
        InMemoryKBAdapter,
        _AuditQueryInput,
        DocumentMetadata,
        DocumentResource,
        _KBSearchInput,
        _RequestContext,
        _handle_audit_query,
        _handle_health_check,
        handle_kb_resource,
        _handle_kb_search,
    ) = _imports()
    adapter = InMemoryKBAdapter(
        documents={
            "doc": DocumentResource(
                metadata=DocumentMetadata(id="doc", title="Runbook", tags=["ops"]),
                content="Full content",
            )
        }
    )
    response = handle_kb_resource(adapter, "doc")
    assert response.metadata.id == "doc"
    assert response.content == "Full content"


def test_audit_query() -> None:
    (
        InMemoryAuditAdapter,
        _InMemoryKBAdapter,
        AuditQueryInput,
        _DocumentMetadata,
        _DocumentResource,
        _KBSearchInput,
        _RequestContext,
        handle_audit_query,
        _handle_health_check,
        _handle_kb_resource,
        _handle_kb_search,
    ) = _imports()
    adapter = InMemoryAuditAdapter(rows=[{"event": "login", "user": "alice"}])
    response = handle_audit_query(adapter, AuditQueryInput(q="login", limit=5))
    assert response.rows
    assert response.rows[0].fields["event"] == "login"
