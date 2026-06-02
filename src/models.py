"""models connecting to database"""

import logging
from typing import Optional
from argon2 import PasswordHasher, exceptions
from sqlalchemy import String, ForeignKey, Boolean, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from utils.constants import ADMIN_ROLE_ID, MOD_ROLE_ID

logger = logging.getLogger("gunicorn.access")


class Base(DeclarativeBase):
    """DeclarativeBase class wrapped around"""


class Role(Base):
    """Role model"""

    __tablename__ = "roles"

    role_id: Mapped[str] = mapped_column(Integer(), primary_key=True)
    role_name: Mapped[str] = mapped_column(String(64))


class User(Base):
    """User model"""

    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(32))
    passwd: Mapped[str] = mapped_column(String(256))
    email: Mapped[str] = mapped_column(String(320))
    bio: Mapped[Optional[str]] = mapped_column(String(256))
    profile_picture: Mapped[Optional[str]] = mapped_column(String(36))
    role_id: Mapped[str] = mapped_column(
        Integer(), ForeignKey("roles.role_id", ondelete="RESTRICT", onupdate="CASCADE")
    )

    usr_role_id: Mapped[Role] = relationship("Role", foreign_keys=[role_id])

    def set_password(self, plain_password):
        """Secures User's password with argon2 hashing algorithm.

        ## Parameters:
            **plain_password** (_str_):
            password in plaintext

        ### Returns:
            **str**:
            hashed password with algorithm argon2
        """
        ph = PasswordHasher()
        hashed_password = ph.hash(plain_password)
        self.passwd = hashed_password
        return hashed_password

    def verify_password(self, plain_password):
        """Verify User's password hash.

        ## Parameters:
            **plain_password** (_str_):
            password in plaintext

        ### Returns:
            _bool_:
            _True_ if password is verified successfully, otherwise _False_.
        """
        ph = PasswordHasher()
        try:
            return ph.verify(self.passwd, plain_password)
        except exceptions.Argon2Error:
            logger.error("Password hash verification failed")
            return False

    def is_privileged(self):
        """Check whether user within User model has privileged role.

        #### Returns:
            **bool**:
            _True_ if user is privileged, otherwise _False_.
        """
        return self.role_id in [ADMIN_ROLE_ID, MOD_ROLE_ID]

    def to_json(self):
        """Represent User class as JSON.

        Returns:
            _str_: JSON string that contains all User class parameters defined.
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


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
