"""Main Flask application factory and error handlers"""

import logging
from flask import Flask, redirect
from config import Config
from extensions import socket, jwt
from auth.routes import auth_bp
from messages.routes import messages_bp
from users.routes import users_bp
from messages import events  # Import to register socket events

logger = logging.getLogger("gunicorn.access")


def create_app():
    """
    App factory function. Define configurations, blueprints and extensions.
    """

    app = Flask(__name__)
    app.config.from_object(Config())

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(users_bp)

    # Initialize extensions
    socket.init_app(
        app,
        cors_allowed_origins=cors_allowed_origins,
        cors_credentials=True,
        engineio_logger=False,
        manage_session=False,
        async_mode="threading"
    )
    jwt.init_app(app)

    # Register error handlers
    @jwt.unauthorized_loader
    def unauthorized_loader_error(error):
        """Custom handler for absence of jwt token when accessing an endpoint"""
        logger.debug(error)
        return redirect("/login")

    @jwt.expired_token_loader
    def expired_token_loader_error(token):
        """Custom handler for expired token provided when accessing an endpoint"""
        token_type = token["type"]
        logger.debug("The %s token has expired", token_type)
        return redirect("/login")

    @jwt.invalid_token_loader
    def invalid_token_loader_error(error):
        """Custom handler for invalid jwt token provided when accessing an endpoint"""
        logger.error(error)
        return redirect("/login")

    return app


def cors_allowed_origins(origin):
    """Allow all origins for Socket.IO CORS"""
    return True
