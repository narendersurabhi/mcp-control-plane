FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml README.md /app/
COPY src /app/src
RUN pip install --upgrade pip && pip install build && python -m build

FROM python:3.11-slim
WORKDIR /app
RUN useradd -u 10001 -m appuser
COPY --from=builder /app/dist/*.whl /app/
RUN pip install --no-cache-dir /app/*.whl
USER appuser
ENV MCP_MODE=stdio
CMD ["python", "-m", "mcp_cp.server"]
