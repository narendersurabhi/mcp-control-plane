# Architecture

## Overview
The control plane is an MCP server that exposes tools, resources, and prompts. It supports both stdio and Streamable HTTP transports. The server is layered with adapters for KB and audit backends, policy enforcement for HTTP, and observability (structured logging, OpenTelemetry tracing, Prometheus metrics).

## Components
- **Server**: MCP SDK server definition with tools/resources/prompts.
- **Adapters**: Pluggable interfaces for KB search and audit queries.
- **Policy**: Scope-based allowlist for tools/resources.
- **HTTP Transport**: Streamable HTTP with bearer auth.
- **Observability**: OTel spans per request, Prometheus metrics, structured logs.

## Data flow
1. Request hits stdio or HTTP transport.
2. Auth + policy (HTTP only).
3. Tool/resource handler with structured logs.
4. Tracing/metrics emitted per invocation.
