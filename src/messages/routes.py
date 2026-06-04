"""Messages routes"""

import logging
from flask import Blueprint, render_template, request
from flask.views import MethodView
from flask_jwt_extended import get_jwt_identity, jwt_required

from messages.services import MessageService
from auth.services import UserService
from core.utils.helpers import log_request
from core.constants import WEBSITE_NAME

messages_bp = Blueprint("messages", __name__)

logger = logging.getLogger("gunicorn.access")
message_service = MessageService()
user_service = UserService()


class MainView(MethodView):
    decorators = [jwt_required()]

    def get(self):
        log_request()

        user_id = get_jwt_identity()
        logger.debug("Current user: %s", user_id)

        message_data = message_service.retrieve_messages(jsonify=True)
        if not message_data and not isinstance(message_data, list):
            logger.error("Failed to display messages.")
            return render_template("errors/error.html", message="Failed to display messages.")

        logger.debug("%s messages retrieved from collection 'messages'.", len(message_data))

        user_data = user_service.get_user_by_id(user_id)
        if not user_data:
            logger.error("Unable to load user info.")
            return render_template(
                "errors/error.html",
                message="Unable to process info about your identity. Pleasy try later.",
            )

        logger.debug("Info about user retrieved successfully: %s", user_data)

        panel = request.args.get("panel", "members")
        members = [u.to_json() for u in user_service.get_user_info()]

        return render_template(
            "messages/index.html",
            msg_data=message_data,
            usr_data=user_data.to_json(),
            web_name=WEBSITE_NAME,
            panel=panel,
            members=members,
        )


messages_bp.add_url_rule(
    "/",
    view_func=MainView.as_view("main"),
    methods=["GET"],
)
