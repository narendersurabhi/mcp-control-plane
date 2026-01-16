from __future__ import annotations

import json
import logging
from collections.abc import MutableMapping
from dataclasses import dataclass
from typing import Any


@dataclass
class LogContext:
    request_id: str
    tool_name: str


class ContextLoggerAdapter(logging.LoggerAdapter[logging.Logger]):
    def process(self, msg: str, kwargs: MutableMapping[str, Any]) -> tuple[str, Any]:
        extra = self.extra or {}
        payload = {
            "message": msg,
            "request_id": extra.get("request_id"),
            "tool_name": extra.get("tool_name"),
        }
        return json.dumps(payload), kwargs


def get_logger(request_id: str, tool_name: str) -> logging.LoggerAdapter[logging.Logger]:
    base = logging.getLogger("mcp_cp")
    return ContextLoggerAdapter(base, {"request_id": request_id, "tool_name": tool_name})


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
