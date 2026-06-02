"""Socket received events handler"""

import logging
from flask import render_template
from flask_socketio import SocketIO, disconnect
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from utils.constants import MSG_MAX_LENGTH
from services import UserService, MessageService

# Create socket handler
socket = SocketIO()

logger = logging.getLogger("gunicorn.access")

# Init custom services
user_service = UserService()
message_service = MessageService()


@socket.on("connect")
def handle_connect():
    """Authenticate client connection with JWT"""
    try:
        verify_jwt_in_request(locations=["cookies"])
        user_id = get_jwt_identity()
        logger.debug("Client connected with user_id: %s", user_id)
    except Exception as e:
        logger.warning("Connection rejected: Invalid or missing JWT token - %s", e)
        disconnect()
        return False


@socket.on("connect_error")
def handle_connect_error(data):
    """Handle failed connection attempts"""
    logger.error("Connection failed: %s", data)


@socket.on("message")
def handle_message(msg):
    """handle initial messages sent via websocket and saves them to database"""
    try:
        verify_jwt_in_request(locations=["cookies"])
        user_id = get_jwt_identity()
    except Exception as e:
        logger.error("Message rejected: JWT verification failed - %s", e)
        disconnect()
        return

    # If recevived message length is more than required
    if len(msg.get("message")) > MSG_MAX_LENGTH:
        logger.debug("Message length limit exceeded")
        socket.emit("message_too_long", {"msg_length": MSG_MAX_LENGTH})
        return

    # Retrieve message
    message = msg.get("message")
    logger.debug("Message received: %s", message)

    # Save to database
    result = message_service.insert_message(message, user_id)
    if not result:
        logger.error("An error occured while inserting message")
        return render_template(
            "error.html", message="An error occured while inserting message"
        )

    username = user_service.get_user_by_id(user_id).username
    logger.debug("Current user: %s", username)

    # Append username info to pass through socket
    msg["username"] = username
    socket.emit("message", msg)


@socket.on("request_message")
def load_messages(cnt):
    """handle socket request to load bunch of messages from database"""
    try:
        verify_jwt_in_request(locations=["cookies"])
    except Exception as e:
        logger.error("Message load rejected: JWT verification failed - %s", e)
        disconnect()
        return

    # Validation piece: handles random other tampered values in global
    # counter variable than numbers
    try:
        int(cnt)
    except ValueError:
        logger.error(
            """Variale 'cnt' value is not expected: not convertable to int
            Current 'cnt' value - %s""",
            cnt,
        )
        return

    # if no messages to load remain sends event via socket
    if message_service.count() <= int(cnt):
        socket.emit("loading_finished")
        return

    # retrieve batch of messages or whatever less that is remained
    messages = message_service.retrieve_messages(
        initial_load=False, counter=int(cnt), jsonify=True
    )
    if not messages:
        logger.error("An error occured while loading messages.")
        return

    logger.debug("%s messages retrieved from collection.", len(messages))

    # sort messages in reversed order by date to send via socket event one by one
    for msg in sorted(messages, key=lambda x: x.message_timestamp, reverse=True):
        message = {
            "username": msg.username,
            "message": msg.message_content,
            "timestamp": str(msg.message_timestamp),
        }
        socket.emit("load", message)
