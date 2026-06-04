"""User profile routes"""

import logging
from flask import Blueprint, abort, flash, redirect, render_template, request, send_file
from flask.views import MethodView
from flask_jwt_extended import get_jwt_identity, jwt_required

from auth.services import UserService
from users.forms import EditProfileForm
from core.utils.helpers import log_request, random_strings_generator
from core.utils.image import ImageHandler
from core.constants import DEFAULT_PROFILE_PICTURE_PATH, WEBSITE_NAME

users_bp = Blueprint("users", __name__)

logger = logging.getLogger("gunicorn.access")
user_service = UserService()


class ProfileView(MethodView):
    decorators = [jwt_required()]

    def _get_user_data(self):
        user_id = get_jwt_identity()
        user_data = user_service.get_user_by_id(user_id)
        if not user_data:
            logger.error("Unable to load user info.")
            return None, None
        return user_id, user_data.to_json()

    def _populate_form(self, form, user_data, csrf_token):
        for field in form:
            if field.name == "csrf_token":
                logger.debug("CSRF token is set")
                field.data = csrf_token
            elif user_data.get(field.name):
                field.data = user_data.get(field.name)
            else:
                field.data = ""

    def get(self):
        log_request()
        user_id, user_data = self._get_user_data()
        if not user_data:
            return render_template(
                "errors/error.html",
                message="Unable to process info about your identity. Pleasy try later.",
            )

        current_user = user_data.get("username")
        logger.debug("Current user: %s", current_user)

        csrf_token = request.cookies.get("csrf_access_token")
        form = EditProfileForm(request.form)
        self._populate_form(form, user_data, csrf_token)

        return render_template(
            "users/profile.html",
            form=form,
            current_user=current_user,
            csrf_token=csrf_token,
            data=user_data,
            web_name=WEBSITE_NAME,
        )

    def post(self):
        log_request()
        user_id, user_data = self._get_user_data()
        if not user_data:
            return render_template(
                "errors/error.html",
                message="Unable to process info about your identity. Pleasy try later.",
            )

        current_user = user_data.get("username")
        csrf_token = request.cookies.get("csrf_access_token")
        form = EditProfileForm(request.form)

        content_clean = request.files["file"].read()
        if content_clean != b"":
            return self._handle_picture_upload(
                content_clean, user_id, user_data, form, current_user, csrf_token
            )

        return self._handle_profile_update(
            user_id, user_data, form, current_user, csrf_token
        )

    def _handle_picture_upload(
        self, content_clean, user_id, user_data, form, current_user, csrf_token
    ):
        image_handler = ImageHandler()
        picture_name = random_strings_generator() + ".jpg"
        save_result = image_handler.save_image(
            content_clean, picture_name, generate_thumbnail=True
        )
        if not save_result["success"]:
            flash(f"Image processing failed: {save_result['error']}")
            return redirect(request.url)

        db_result = user_service.update_user(user_id, profile_picture=picture_name)
        if not db_result:
            logger.debug("Profile picture update failed.")
            image_handler.delete_image(picture_name, delete_thumbnail=True)
            flash("Unable to renew your profile picture. Try again later.")
            return redirect(request.url)

        if user_data.get("profile_picture") is not None:
            image_handler.delete_image(
                user_data.get("profile_picture"), delete_thumbnail=True
            )

        return render_template(
            "users/profile.html",
            form=form,
            current_user=current_user,
            csrf_token=csrf_token,
            data=user_data,
        )

    def _handle_profile_update(self, user_id, user_data, form, current_user, csrf_token):
        if not form.validate():
            logger.debug("Validation of profile edit form's input failed")
            self._populate_form(form, user_data, csrf_token)
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

            if user_service.get_user_info(**{field.name: field.data}):
                flash("These credentials are already in use.")
                return redirect(request.url)

            newvalues[field.name] = field.data

        if newvalues:
            logger.debug("Values to update: %s", len(newvalues))
            result = user_service.update_user(user_id, update_dict=newvalues)
            if not result:
                logger.debug("Data update failed")
                return render_template(
                    "errors/error.html",
                    message="Unable to renew your info. Try again later.",
                )
            logger.info("User info updated successfully")

        return redirect(request.url)


class PublicProfileView(MethodView):
    decorators = [jwt_required()]

    def get(self, user):
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


class ProfilePictureView(MethodView):
    decorators = [jwt_required()]

    def get(self, user):
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


users_bp.add_url_rule(
    "/myprofile",
    view_func=ProfileView.as_view("profile"),
    methods=["GET", "POST"],
)
users_bp.add_url_rule(
    "/profile/<user>",
    view_func=PublicProfileView.as_view("public_profile"),
    methods=["GET"],
)
users_bp.add_url_rule(
    "/profile-picture/<user>",
    view_func=ProfilePictureView.as_view("profile_picture"),
    methods=["GET"],
)
