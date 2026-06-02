"""Services to execute database transactions"""

import os
import logging

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from models import User, Message
from utils.helpers import random_strings_generator
from utils.constants import MSG_LOAD_BATCH, ADMIN_ROLE_ID, USER_ROLE_ID

# Initialise logger
logger = logging.getLogger("gunicorn.access")

# Retrieve environment variables
POSTGRES_USER = os.getenv("POSTGRES_USERNAME")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DATABASE = os.getenv("PGDATABASE")
POSTGRES_HOSTNAME = os.getenv("POSTGRES_HOSTNAME")

# Connect to database
conn_string = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOSTNAME}:5432/{POSTGRES_DATABASE}"
engine = create_engine(conn_string)


class UserService:
    """Operate user-related transactions"""

    def __init__(self):
        self.session = sessionmaker(engine)

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
        """Insert row in a database which with all user info provided.

        ## Parameters:
            **username** (_str_): 
            Username to insert. <br>

            **password** (_str_): 
            Plain text password. Will be hashed with argon2 algorithm. <br>

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
            User unique identification string. <br>

            **update_dict** (_dict_, optional): 
            Dictionary of values to be updated, according to column names. Required to
            use only either `update_dict` or specify parameters separately. Defaults to None.

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



class MessageService:
    """Operate messages-related transactions"""

    def __init__(self):
        self.session = sessionmaker(engine)

    def count(self):
        """Return total count of messages stored in database. Return _None_
        if exception is caught.
        """
        session = self.session()
        logger.debug("Starting a session.")

        try:
            total_count = session.query(Message).count()
            return total_count
        except SQLAlchemyError:
            logger.error("An error occured while establishing conection with PostgreSQL instance.")
            return None
        finally:
            logger.debug("Closing session.")
            session.close()

    def insert_message(self, message, user_id):
        """Insert all provided message info to database.

        ## Parameters:
            **message_content** (_str_): 
            Message to be inserted. <br>

            **user_id** (_str_): 
            Author's unique identifier.

        ### Returns:
            _bool_:
            _True_ if insert operation is completed successfully, otherwise _False_.
        """
        session = self.session()
        logger.debug("Starting a session.")

        try:
            new_message = Message(
                message_id=random_strings_generator(),
                message_content=message,
                message_timestamp=str(datetime.now().timestamp()),
                user_id=user_id
            )

            session.add(new_message)
            session.commit()
            return True
        except SQLAlchemyError:
            logger.error("An error occured while establishing conection with PostgreSQL instance.")
            return False
        finally:
            logger.debug("Closing session.")
            session.close()

    def retrieve_messages(self, initial_load=True, counter=None, jsonify=False):
        r"""Retrieve messages from database ready to be rendered on page.

        ## Parameters:
            **initial_load** (_bool_, optional):
            Set _True_ when application is accessing rows initially i.e. 
            when it is needed to load only newest batch of messages,
            otherwise parameter needs to be specified as _False_. 
            Defaults to _True_. <br>

            **counter** (_str_, optional): 
            Counter of already loaded messages. Applies only if `inital_load`
            is set to _False_. Defaults to _None_. <br>

            **jsonify** (bool, optional): 
            Set this option to _True_ additionally if it is needed to return 
            JSON representation on an object. Defaults to False.

        ### Returns:
            _List\[Row\[Tuple\[Message, User\]\]\]_ | _dict_: 
            retrieved messages as join result of tables messages and users.
        """
        session = self.session()
        logger.debug("Starting a session.")

        try:
            query = session.query(
                Message.message_id,
                Message.message_content,
                Message.message_timestamp,
                Message.message_edited,
                User.user_id,
                User.username
            ).join(User, Message.user_id==User.user_id)

            if initial_load:
                rows_returning_query = query.offset(
                    0
                    if session.query(Message).count() < MSG_LOAD_BATCH
                    else session.query(Message).count() - MSG_LOAD_BATCH
                ).limit(MSG_LOAD_BATCH)
            else:
                rows_returning_query = query.offset(
                    0
                    if session.query(Message).count() < MSG_LOAD_BATCH + counter
                    else session.query(Message).count() - MSG_LOAD_BATCH - counter
                ).limit(MSG_LOAD_BATCH)

            result = rows_returning_query.all()
            logger.debug("%s rows retrieved: %s", len(result), result)
        except SQLAlchemyError:
            logger.error("An error occured while establishing conection with PostgreSQL instance.")
            return None
        finally:
            logger.debug("Closing session.")
            session.close()

        if jsonify:
            for index, message in enumerate(result):
                result[index] = message._mapping

        return result
