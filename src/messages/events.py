"""Socket.IO events for messages"""

import logging
from flask_socketio import disconnect
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from extensions import socket
from core.constants import MSG_MAX_LENGTH
from auth.services import UserService
from messages.services import MessageService

logger = logging.getLogger("gunicorn.access")

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
    """Handle initial messages sent via websocket and saves them to database"""
    try:
        verify_jwt_in_request(locations=["cookies"])
        user_id = get_jwt_identity()
    except Exception as e:
        logger.error("Message rejected: JWT verification failed - %s", e)
        disconnect()
        return

    if len(msg.get("message")) > MSG_MAX_LENGTH:
        logger.debug("Message length limit exceeded")
        socket.emit("message_too_long", {"msg_length": MSG_MAX_LENGTH})
        return

    message = msg.get("message")
    logger.debug("Message received: %s", message)

    result = message_service.insert_message(message, user_id)
    if not result:
        logger.error("An error occured while inserting message")
        return

    username = user_service.get_user_by_id(user_id).username
    logger.debug("Current user: %s", username)

    msg["username"] = username
    socket.emit("message", msg)


@socket.on("request_message")
def load_messages(cnt):
    """Handle socket request to load bunch of messages from database"""
    try:
        verify_jwt_in_request(locations=["cookies"])
    except Exception as e:
        logger.error("Message load rejected: JWT verification failed - %s", e)
        disconnect()
        return

    try:
        int(cnt)
    except ValueError:
        logger.error(
            """Variable 'cnt' value is not expected: not convertable to int
            Current 'cnt' value - %s""",
            cnt,
        )
        return

    if message_service.count() <= int(cnt):
        socket.emit("loading_finished")
        return

    messages = message_service.retrieve_messages(
        initial_load=False, counter=int(cnt), jsonify=True
    )
    if not messages:
        logger.error("An error occured while loading messages.")
        return

    logger.debug("%s messages retrieved from collection.", len(messages))

    for msg in sorted(messages, key=lambda x: x.get("message_timestamp", 0), reverse=True):
        message = {
            "username": msg.get("username"),
            "message": msg.get("message_content"),
            "timestamp": msg.get("message_timestamp").isoformat(),
        }
        socket.emit("load", message)
