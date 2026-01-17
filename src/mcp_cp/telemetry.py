from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Histogram

SERVICE_NAME = "mcp-control-plane"

request_count = Counter("request_count", "Total MCP requests", ["method", "tool"])
request_latency_ms = Histogram(
    "request_latency_ms",
    "Latency per MCP request",
    ["method", "tool"],
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2000),
)
tool_error_count = Counter("tool_error_count", "Tool errors", ["tool"])


def configure_tracing() -> None:
    resource = Resource.create({"service.name": SERVICE_NAME})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


@contextmanager
def request_span(method: str, tool_name: str) -> Iterator[dict[str, float]]:
    tracer = trace.get_tracer(__name__)
    start = time.perf_counter()
    with tracer.start_as_current_span("mcp.request") as span:
        span.set_attribute("mcp.method", method)
        span.set_attribute("tool.name", tool_name)
        outcome = "success"
        try:
            yield {"start": start}
        except Exception:
            outcome = "error"
            span.set_attribute("outcome", outcome)
            raise
        finally:
            latency_ms = (time.perf_counter() - start) * 1000
            span.set_attribute("latency_ms", latency_ms)
            span.set_attribute("outcome", outcome)
            request_count.labels(method=method, tool=tool_name).inc()
            request_latency_ms.labels(method=method, tool=tool_name).observe(latency_ms)
            if outcome == "error":
                tool_error_count.labels(tool=tool_name).inc()
