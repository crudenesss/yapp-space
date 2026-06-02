"""Message services for database operations"""

import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from extensions import SessionLocal
from messages.models import Message
from auth.models import User
from core.utils.helpers import random_strings_generator
from core.constants import MSG_LOAD_BATCH

logger = logging.getLogger("gunicorn.access")


class MessageService:
    """Operate messages-related transactions"""

    def __init__(self):
        self.session = SessionLocal

    def count(self):
        """Return total count of messages stored in database."""
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
            **message** (_str_): 
            Message to be inserted.

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
            Set _True_ when application is accessing rows initially. Defaults to _True_.

            **counter** (_str_, optional): 
            Counter of already loaded messages. Applies only if `inital_load`
            is set to _False_. Defaults to _None_.

            **jsonify** (bool, optional): 
            Set this option to _True_ additionally if it is needed to return 
            JSON representation. Defaults to False.

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
