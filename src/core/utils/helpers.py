"""Miscellaneous functions to use in application"""

import uuid
import logging
from flask import current_app, request

logger = logging.getLogger("gunicorn.access")


def random_strings_generator():
    """Generate random strings for filenames and other ids.

    ### Returns:
        _string_: 
        randomly generated uuid.
    """
    newname = str(uuid.uuid4())
    return newname


def log_request():
    """Debug-level log to dump useful info about received requests"""
    with current_app.app_context():
        data = {
            "access_route": request.access_route,
            "args": request.args,
            "base_url": request.base_url,
            "content_encoding": request.content_encoding,
            "endpoint": request.endpoint,
            "files": request.files,
            "headers": request.headers,
            "method": request.method,
        }

    logger.debug("The request has reached the server with parameters: %s", data)
