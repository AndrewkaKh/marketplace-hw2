from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UserContext:
    user_id: str
    role: str  # USER | SELLER | ADMIN


current_user: ContextVar[Optional[UserContext]] = ContextVar("current_user", default=None)


def get_current_user() -> Optional[UserContext]:
    return current_user.get()