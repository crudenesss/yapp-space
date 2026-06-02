"""main application file"""

import logging
from os import getenv
from datetime import timedelta
from flask import Flask, redirect, request
from flask_jwt_extended import JWTManager

# from forms import MessageForm
from utils.constants import SESSION_EXPIRY
from views import views_bp
from events import socket


class Config(object):
    """Base Flask app config."""
    SECRET_KEY = getenv("FLASK_SECRET_KEY")

    # JWT
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=SESSION_EXPIRY)
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_CSRF_CHECK_FORM = True

    # Content validation
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024


def cors_allowed_origins(origin):
    """Allow all origins for Socket.IO CORS"""
    return True


def create_app():
    """
    App factory function. Define configurations, blueprints and 
    other extensions.
    """

    # Define app
    app = Flask(__name__)
    app.config.from_object(Config())

    # Blueprints
    app.register_blueprint(views_bp)

    # Init extensions
    socket.init_app(
        app, 
        cors_allowed_origins=cors_allowed_origins,
        cors_credentials=True,
        engineio_logger=False,
        manage_session=False,
        async_mode="threading"
    )
    jwt.init_app(app)

    return app


# Create jwt manager handler
jwt = JWTManager()

logger = logging.getLogger("gunicorn.access")


# Custom exceptions for error responses
@jwt.unauthorized_loader
def unauthorized_loader_error(error):
    """Custom handler for abscence of jwt token when accessing an endpoint"""
    logger.debug(error)
    return redirect("/login")


@jwt.expired_token_loader
def expired_token_loader_error(token):
    """Custom handler for expired token provided when accesssing an endpoint"""
    token_type = token["type"]
    logger.debug("The %s token has expired", token_type)
    return redirect("/login")


@jwt.invalid_token_loader
def invalid_token_loader_error(error):
    """Custom handler for invalid jwt token provided when accessing an endpoint"""
    logger.error(error)
    return redirect("/login")
