from datetime import datetime, timezone


def agora_iso() -> str:
    """Data/hora atual em UTC no formato ISO 8601 (ex.: 2026-10-20T14:32:05Z)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
