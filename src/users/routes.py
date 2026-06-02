"""User profile routes"""

import logging
from flask import Blueprint, abort, flash, redirect, render_template, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from auth.services import UserService
from users.forms import EditProfileForm
from core.utils.helpers import log_request, random_strings_generator
from core.utils.image import ImageHandler
from core.constants import DEFAULT_PROFILE_PICTURE_PATH, WEBSITE_NAME

users_bp = Blueprint("users", __name__)

logger = logging.getLogger("gunicorn.access")
user_service = UserService()


@users_bp.route("/myprofile", methods=["GET", "POST"])
@jwt_required()
def profile():
    """Display profile page"""

    log_request()

    user_id = get_jwt_identity()

    user_data = user_service.get_user_by_id(user_id)
    if not user_data:
        logger.error("Unable to load user info.")
        return render_template(
            "errors/error.html",
            message="Unable to process info about your identity. Pleasy try later.",
        )

    user_data = user_data.to_json()
    current_user = user_data.get("username")
    logger.debug("Current user: %s", current_user)

    csrf_token = request.cookies.get("csrf_access_token")
    form = EditProfileForm(request.form)

    if request.method != "POST":

        for field in form:
            if field.name == "csrf_token":
                logger.debug("CSRF token is set")
                field.data = csrf_token
            elif user_data.get(field.name):
                field.data = user_data.get(field.name)
            else:
                field.data = ""

        return render_template(
            "users/profile.html",
            form=form,
            current_user=current_user,
            csrf_token=csrf_token,
            data=user_data,
            web_name=WEBSITE_NAME,
        )

    content_clean = request.files["file"].read()
    if content_clean != b"":

        # Use ImageHandler for image processing
        image_handler = ImageHandler()
        picture_name = random_strings_generator()
        
        save_result = image_handler.save_image(content_clean, picture_name, generate_thumbnail=True)
        if not save_result["success"]:
            flash(f"Image processing failed: {save_result['error']}")
            return redirect(request.url)

        # Update user profile picture in database
        db_result = user_service.update_user(user_id, profile_picture=picture_name)
        if not db_result:
            logger.debug("Profile picture update failed.")
            image_handler.delete_image(picture_name, delete_thumbnail=True)
            flash("Unable to renew your profile picture. Try again later.")
            return redirect(request.url)

        # Delete old profile picture if it exists
        if user_data.get("profile_picture") is not None:
            image_handler.delete_image(user_data.get("profile_picture"), delete_thumbnail=True)

        return render_template(
            "users/profile.html",
            form=form,
            current_user=current_user,
            csrf_token=csrf_token,
            data=user_data,
        )

    if not form.validate():
        logger.debug("Validation of profile edit form's input failed")

        for field in form:
            if field.name == "csrf_token":
                logger.debug("CSRF token is set")
                field.data = csrf_token
            elif user_data.get(field.name):
                field.data = user_data.get(field.name)
            else:
                field.data = ""

        return render_template(
            "users/profile.html",
            form=form,
            current_user=current_user,
            csrf_token=csrf_token,
            data=user_data,
        )

    newvalues = {}

    for field in form:

        if field.name not in ["username", "password", "email", "bio"]:
            continue

        if field.data == user_data[field.name]:
            continue

        if field.name not in ["username", "email"]:
            newvalues[field.name] = field.data
            continue

        kwargs = {field.name: field.data}

        if user_service.get_user_info(**kwargs):
            flash("These credentials are already in use.")
            return redirect(request.url)

        newvalues[field.name] = field.data

    if len(newvalues) > 0:
        logger.debug("Values to update: %s", len(newvalues))

        result = user_service.update_user(user_id, update_dict=newvalues)
        if not result:
            logger.debug("Data update failed")
            return render_template(
                "errors/error.html", message="Unable to renew your info. Try again later."
            )

        logger.info("User info updated successfully")

    return redirect(request.url)


@users_bp.route("/profile/<user>", methods=["GET"])
@jwt_required()
def public_profile(user):
    """Display profile page in public mode"""

    log_request()

    user_id = get_jwt_identity()
    current_user_info = user_service.get_user_by_id(user_id)
    if not current_user_info:
        logger.error("Unable to load user info.")
        return render_template(
            "errors/error.html",
            message="Unable to process info about your identity. Pleasy try later.",
        )

    current_user = current_user_info.username
    logger.debug("Current user: %s", current_user)

    if not user_service.get_user_info(username=user):
        logger.debug("The username profile that was tried to access does not exist")
        return abort(404)

    logger.debug("Info about user retrieved successfully")
    user_data = user_service.get_user_info(username=user)[0].to_json()

    return render_template(
        "users/profile_public.html",
        current_user=current_user,
        data=user_data,
        web_name=WEBSITE_NAME,
    )


@users_bp.route("/profile-picture/<user>", methods=["GET"])
@jwt_required()
def profile_picture(user):
    """Retrieve users' profile pictures"""

    log_request()

    user_info = user_service.get_user_info(username=user)
    if not user_info:
        logger.error("Unable to load user info.")
        return render_template(
            "errors/error.html",
            message="Unable to process info about your identity. Pleasy try later.",
        )

    profile_picture_name = user_info[0].profile_picture

    if profile_picture_name is None:
        logger.debug("Profile picture not set: using default.")
        return send_file(DEFAULT_PROFILE_PICTURE_PATH)

    logger.debug("Profile picture is returned for: %s", user)
    image_handler = ImageHandler()
    return send_file(image_handler.get_image_path(profile_picture_name))
