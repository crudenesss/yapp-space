"""Auth services for user operations"""

import logging
from sqlalchemy.exc import SQLAlchemyError
from extensions import SessionLocal
from auth.models import User
from core.utils.helpers import random_strings_generator
from core.constants import ADMIN_ROLE_ID, USER_ROLE_ID

logger = logging.getLogger("gunicorn.access")


class UserService:
    """Operate user-related transactions"""

    def __init__(self):
        self.session = SessionLocal

    def get_user_by_id(self, identity):
        """Return User object by its identifier.

        ## Parameters:
            **identity** (_str_):
            User unique identifier.

        ### Returns:
            _User_:
            User object. _None_ if exception caught.
        """
        session = self.session()
        logger.debug("Starting a session.")

        try:
            result = session.query(User).get(identity)
            return result
        except SQLAlchemyError:
            logger.error("An error occured while establishing conection with PostgreSQL instance.")
            return None
        finally:
            logger.debug("Closing session.")
            session.close()

    def get_user_info(self, **kwargs):
        r"""Retrieve list of users from connected database. Provide additional
        arguments to filter results by column (i.e. `WHERE` clause).

        ### Returns:
            _List\[User\]_:
            list of User objects. _None_ if an exception is caught.
        """
        session = self.session()
        logger.debug("Starting a session.")

        try:
            if kwargs:
                results = session.query(User).filter_by(**kwargs).all()
            else:
                results = session.query(User).all()

            return results
        except SQLAlchemyError:
            logger.error("An error occured while establishing conection with PostgreSQL instance.")
            return None
        finally:
            logger.debug("Closing session.")
            session.close()

    def insert_user(self, username, password, email):
        """Insert row in a database with all user info provided.

        ## Parameters:
            **username** (_str_): 
            Username to insert.

            **password** (_str_): 
            Plain text password. Will be hashed with argon2 algorithm.

            **email** (_str_): 
            Email.

        ### Returns:
            _bool_:
            _True_ if operation is successful, otherwise _False_.
        """
        session = self.session()
        logger.debug("Starting a session.")

        try:
            if session.query(User).all():
                role = USER_ROLE_ID
            else:
                role = ADMIN_ROLE_ID

            new_user = User(
                user_id=random_strings_generator(),
                username=username,
                email=email,
                role_id=role,
            )
            new_user.set_password(password)

            session.add(new_user)
            session.commit()
            return True
        except SQLAlchemyError:
            logger.error("An error occured while establishing conection with PostgreSQL instance.")
            return False
        finally:
            logger.debug("Closing session.")
            session.close()

    def update_user(self, identity, update_dict=None, **kwargs):
        """Update User info with provided arguments.

        ## Parameters:
            **identity** (_str_): 
            User unique identification string.

            **update_dict** (_dict_, optional): 
            Dictionary of values to be updated, according to column names. Defaults to None.

        ### Returns:
            _bool_: 
            _True_ if update operation completed successfully, otherwise _False_.
        """
        session = self.session()
        logger.debug("Starting a session.")

        try:
            if update_dict:
                result = session.query(User).filter_by(user_id=identity).update(update_dict)
            elif kwargs:
                result = session.query(User).filter_by(user_id=identity).update(kwargs)
            else:
                logger.debug("No update to execute, as parameters were not provided.")
                return False

            session.commit()
        except SQLAlchemyError:
            logger.error("An error occured while establishing conection with PostgreSQL instance.")
            return False
        finally:
            logger.debug("Closing session.")
            session.close()

        if result < 1:
            logger.debug("No rows affected after update operation.")
            return False

        logger.debug("User info updated successfully: %s row(s) affected.", result)
        return True
