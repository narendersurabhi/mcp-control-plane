# Runbook

## Debug a slow tool call using traces
1. Identify the request ID from logs (every log line includes `request_id`).
2. Open Jaeger (from docker-compose) and search for traces by `tool.name` or `mcp.method`.
3. Inspect spans to find the slowest segment (attributes include `latency_ms`).
4. Cross-reference Prometheus metrics (`request_latency_ms`) to see if latency is systemic.
5. If the tool is the culprit, verify upstream adapters (KB or audit) and apply throttling or caching.

## Common commands
```bash
make run-stdio
make run-http
make compose-up
make compose-down
```
