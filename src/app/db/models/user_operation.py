import enum
from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserOperationType(str, enum.Enum):
    CREATE_ORDER = "CREATE_ORDER"
    UPDATE_ORDER = "UPDATE_ORDER"


class UserOperation(Base):
    __tablename__ = "user_operations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    operation_type: Mapped[UserOperationType] = mapped_column(
        Enum(UserOperationType, name="user_operation_type"), nullable=False
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)