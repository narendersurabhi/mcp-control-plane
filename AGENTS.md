# Agent Change Log

## 2026-01-16
- Initialized project structure with src layout, tooling config, and docs.
- Added MCP server implementation with tools/resources/prompts, logging, policy, HTTP mode, tracing, and metrics.
- Added tests, deployment assets (Docker, Helm, docker-compose), and GitHub workflows.
- Adjusted typing and lint configuration to satisfy ruff and mypy checks.
- Added test helpers to allow running tests without installed dependencies in constrained environments.
- Resolved mypy complaints in adapters, server decorators, and test import typing.
- Sorted test imports to satisfy ruff linting.
- Tweaked server decorator ignores and stdio initialization typing to satisfy mypy.
- Re-applied server casts for mypy and ran black formatting sweep.
