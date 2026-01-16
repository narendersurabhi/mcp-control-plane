from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from mcp_cp.models import (
    AuditQueryResponse,
    DocumentMetadata,
    DocumentResource,
    KBSearchResponse,
    KBSearchResult,
)


class KBAdapter(Protocol):
    def search(self, query: str, top_k: int) -> KBSearchResponse: ...

    def get_document(self, doc_id: str) -> DocumentResource: ...


class AuditAdapter(Protocol):
    def query(self, q: str, limit: int) -> AuditQueryResponse: ...


@dataclass
class InMemoryKBAdapter:
    documents: dict[str, DocumentResource]

    def search(self, query: str, top_k: int) -> KBSearchResponse:
        results = []
        for doc in self.documents.values():
            if query.lower() in doc.metadata.title.lower() or query.lower() in doc.content.lower():
                results.append(
                    KBSearchResult(
                        id=doc.metadata.id,
                        title=doc.metadata.title,
                        snippet=doc.content[:120],
                        score=0.9,
                    )
                )
        return KBSearchResponse(results=results[:top_k])

    def get_document(self, doc_id: str) -> DocumentResource:
        if doc_id not in self.documents:
            raise KeyError(f"Document {doc_id} not found")
        return self.documents[doc_id]


@dataclass
class InMemoryAuditAdapter:
    rows: list[dict[str, object]]

    def query(self, q: str, limit: int) -> AuditQueryResponse:
        filtered = [row for row in self.rows if q.lower() in str(row).lower()]
        return AuditQueryResponse(rows=[{"fields": row} for row in filtered[:limit]])


def default_kb_adapter() -> InMemoryKBAdapter:
    docs = {
        "intro": DocumentResource(
            metadata=DocumentMetadata(id="intro", title="Welcome", tags=["intro"]),
            content="Welcome to the MCP control plane knowledge base.",
        )
    }
    return InMemoryKBAdapter(documents=docs)


def default_audit_adapter() -> InMemoryAuditAdapter:
    return InMemoryAuditAdapter(rows=[{"event": "startup", "status": "ok"}])
