from __future__ import annotations

from dataclasses import dataclass

DEFAULT_SCOPE_MAP = {
    "read": {"kb.search", "kb.resource", "health.check"},
    "audit": {"audit.query", "health.check"},
}


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str | None = None


class ScopePolicy:
    def __init__(self, scope_map: dict[str, set[str]] | None = None) -> None:
        self.scope_map = scope_map or DEFAULT_SCOPE_MAP

    def allows(self, scope: str, action: str) -> PolicyDecision:
        allowed_actions = self.scope_map.get(scope, set())
        if action in allowed_actions:
            return PolicyDecision(allowed=True)
        return PolicyDecision(
            allowed=False, reason=f"scope '{scope}' does not allow '{action}'"
        )
