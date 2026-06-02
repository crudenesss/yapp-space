"""Message model"""

from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import Base
from auth.models import User


class Message(Base):
    """Message model"""

    __tablename__ = "messages"

    message_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    message_content: Mapped[str] = mapped_column(String(4096))
    message_timestamp: Mapped[str] = mapped_column(String(32))
    message_edited: Mapped[bool] = mapped_column(Boolean(), default=False)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.user_id", onupdate="CASCADE")
    )

    msg_user_id: Mapped[User] = relationship("User", foreign_keys=[user_id])

    def to_json(self):
        """Represent Message class as JSON.

        Returns:
            _str_: JSON string that contains all Message class parameters defined.
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
