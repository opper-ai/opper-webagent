from threading import Lock
from typing import List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

@dataclass
class StatusEntry:
    timestamp: datetime
    action: str
    details: str = None
    screenshot_path: Optional[str] = None

class StatusManager:
    def __init__(self, status_callback: Optional[Callable[[str, str], None]] = None):
        self._status_lock = Lock()
        self._status_log: List[StatusEntry] = []
        self._status_callback = status_callback

    def update(self, action: str, details: str = None, screenshot_path: Optional[str] = None):
        """Update the current status of the web agent."""
        with self._status_lock:
            self._status_log.append(StatusEntry(
                timestamp=datetime.now(),
                action=action,
                details=details,
                screenshot_path=screenshot_path
            ))
        if self._status_callback:
            self._status_callback(action, details)

    def get_current(self) -> dict:
        """Get the current status of the web agent."""
        with self._status_lock:
            if self._status_log:
                latest = self._status_log[-1]
                return {
                    "action": latest.action,
                    "details": latest.details,
                    "screenshot_path": latest.screenshot_path
                }
            return {"action": None, "details": None, "screenshot_path": None}

    def get_history(self) -> List[StatusEntry]:
        """Get the full history of status updates."""
        with self._status_lock:
            return self._status_log.copy() 