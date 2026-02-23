"""
Security audit logging with structured JSON-Lines.
"""
import json
from datetime import datetime, timezone
from typing import Any, Dict

from .config import get_config_dir


class AuditLogger:
    """Writes structured JSONL audit logs without sensitive data."""
    def __init__(self):
        self.log_file = get_config_dir() / "audit.jsonl"
        
    def log(self, event_type: str, **kwargs: Any) -> None:
        """Log a structured security/operation event."""
        entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "details": kwargs
        }
        
        # Ensure no passwords or deep secrets are in kwargs
        for key in ["password", "token", "secret", "key"]:
            if key in entry["details"]:
                entry["details"][key] = "*****"
                
        try:
            with self.log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            try:
                import sys
                sys.stderr.write(f"[TermBackup Audit Error] Failed to write log: {e}\n")
                fallback = get_config_dir() / "audit_fallback.log"
                with fallback.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception:
                pass

def get_audit_log(last_n: int = 50) -> list[Dict[str, Any]]:
    """Retrieve the last N events from the audit log."""
    log_file = get_config_dir() / "audit.jsonl"
    if not log_file.exists():
        return []
        
    lines = []
    try:
        with log_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            
        parsed = []
        for line in lines[-last_n:]:
            if line.strip():
                parsed.append(json.loads(line))
        return parsed
    except Exception:
        return []
