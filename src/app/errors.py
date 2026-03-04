from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ApiError(Exception):
    status_code: int
    error_code: str
    message: str
    details: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }
