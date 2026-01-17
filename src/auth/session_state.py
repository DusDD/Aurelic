from __future__ import annotations

class SessionState:
    token: str | None = None

SESSION = SessionState()
