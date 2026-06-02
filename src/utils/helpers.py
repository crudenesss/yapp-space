"""misc functions to use in application"""

import uuid
import logging
import io
import magic
from flask import current_app, request
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger("gunicorn.access")


# Functions to use with uploaded images
def verify_image(data):
    """Verify the received image as having appropriate format and no
    corruptions/malicious modifications and finally appropriate dimensions.

    ## Parameters:
        **data** (_bytes_): 
        full file stored in bytestream
    ### Returns:
        _bool_: 
        _True_ if image is appropriate format and not corrupted, otherwise _False_.
    """

    allowed_image_types = ["image/jpeg", "image/png"]

    content_type = magic.from_buffer(data, mime=True)
    if content_type not in allowed_image_types:
        logger.error("Error while verifying image: signature does not match allowed formats")
        return False

    logger.debug("Signature is verified")

    try:
        image = Image.open(io.BytesIO(data))
        image.verify()
        logger.debug("Image's integrity is verified")
    except UnidentifiedImageError:
        logger.debug("Error while verifying image: tampered extension or corrupted file")
        return False
    except OSError:
        logger.debug("Error while verifying image: the file is likely truncated")
        return False

    if any(x > y for x, y in zip((200, 200), image.size)):

        logger.debug("Unacceptable resolution of the uploaded photo: %s", image.size)
        return False

    logger.debug("Image resolution is verified")
    return True


# To mitigate security risks, all the received files from client side
# will be renamed to some random uuid
def random_strings_generator():
    """Generate random strings for filenames and other ids.

    ### Returns:
        _string_: 
        randomly generated uuid.
    """
    newname = str(uuid.uuid4())
    return newname


# Function to send custom log messages for each instances
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
