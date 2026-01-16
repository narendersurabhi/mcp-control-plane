import pytest


def test_trace_created_for_tool() -> None:
    pytest.importorskip("pydantic")
    pytest.importorskip("mcp")
    opentelemetry = pytest.importorskip("opentelemetry")
    trace = opentelemetry.trace
    TracerProvider = pytest.importorskip("opentelemetry.sdk.trace").TracerProvider
    trace_export = pytest.importorskip("opentelemetry.sdk.trace.export")
    InMemorySpanExporter = trace_export.InMemorySpanExporter
    SimpleSpanProcessor = trace_export.SimpleSpanProcessor
    from mcp_cp.server import handle_health_check

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    handle_health_check("1.0.0")

    spans = exporter.get_finished_spans()
    assert spans
    assert spans[0].attributes.get("tool.name") == "health.check"
