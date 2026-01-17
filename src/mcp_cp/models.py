from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    status: str
    deps: dict[str, str]
    version: str


class KBSearchInput(BaseModel):
    query: str
    top_k: int = 5


class KBSearchResult(BaseModel):
    id: str
    title: str
    snippet: str
    score: float


class KBSearchResponse(BaseModel):
    results: list[KBSearchResult]


class AuditQueryInput(BaseModel):
    q: str
    limit: int = 50


class AuditQueryRow(BaseModel):
    fields: dict[str, Any]


class AuditQueryResponse(BaseModel):
    rows: list[AuditQueryRow]


class DocumentMetadata(BaseModel):
    id: str
    title: str
    tags: list[str] = Field(default_factory=list)


class DocumentResource(BaseModel):
    metadata: DocumentMetadata
    content: str


class ErrorResponse(BaseModel):
    code: int
    message: str
    data: dict[str, Any] | None = None
