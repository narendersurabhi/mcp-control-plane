# Security

## Transport security
- HTTP mode requires `Authorization: Bearer <token>` with token from `MCP_BEARER_TOKEN`.
- Stdio mode is intended for local trusted use.

## Access control
- HTTP requests use a scope-based allowlist policy (`read`, `audit`).
- Deny-by-default for tools/resources not explicitly allowed.

## Secrets
- Do not commit tokens.
- Configure secrets via environment variables or Kubernetes secrets.

## Vulnerability management
- CI includes SBOM generation and container scanning on tags.
