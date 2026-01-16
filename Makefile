.PHONY: install lint typecheck test coverage run-stdio run-http compose-up compose-down

install:
	pip install -e .[dev]

lint:
	ruff check src tests
	ruff format --check src tests

typecheck:
	mypy src tests

test:
	pytest -q

coverage:
	coverage run -m pytest -q
	coverage report

run-stdio:
	MCP_MODE=stdio python -m mcp_cp.server

run-http:
	MCP_MODE=http python -m mcp_cp.server

compose-up:
	docker compose -f deploy/compose/docker-compose.yml up -d

compose-down:
	docker compose -f deploy/compose/docker-compose.yml down
