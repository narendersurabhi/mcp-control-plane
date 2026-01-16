# mcp-control-plane

Production-grade MCP server with stdio and HTTP transport, observability, and deployment assets.

## Features
- MCP tools/resources/prompts for health, KB search, and audit queries.
- Structured logging with request and tool context.
- OpenTelemetry tracing + Prometheus metrics.
- HTTP mode with bearer auth and scope-based policy.
- Docker, docker-compose, and Helm deployment assets.

## Quickstart
```bash
make install
make run-stdio
```

### HTTP mode
```bash
export MCP_MODE=http
export MCP_BEARER_TOKEN=devtoken
python -m mcp_cp.server
```

Requests must include `Authorization: Bearer <token>` and an `X-MCP-Scope` header
(e.g. `read` or `audit`) to satisfy policy checks.

## Local deployment (docker-compose)
```bash
make compose-up
```

## Kubernetes (Helm)
```bash
helm install mcp-control-plane deploy/helm/chart \
  --set image.tag=latest \
  --set env.MCP_BEARER_TOKEN=changeme
```

## Development
```bash
make lint
make typecheck
make test
make coverage
```
