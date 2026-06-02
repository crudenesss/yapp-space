"""routes for app"""

import os
import logging
from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
)
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
)

from services import UserService, MessageService
from decorators import privilege_required
from forms import RegForm, LogForm, EditProfileForm

from utils.constants import (
    PROFILE_PICTURE_STORAGE_PATH,
    DEFAULT_PROFILE_PICTURE_PATH,
    WEBSITE_NAME,
)
from utils.helpers import (
    random_strings_generator,
    log_request,
    verify_image,
)

# Blueprint initialization
views_bp = Blueprint("routes", __name__)

# Init root logger
logger = logging.getLogger("gunicorn.access")

# Init custom services
user_service = UserService()
message_service = MessageService()


@views_bp.route("/", methods=["GET"])
@jwt_required()
def main():
    """Root page where the chat operates"""

    log_request()

    user_id = get_jwt_identity()
    logger.debug("Current user: %s", user_id)

    # Retrieve messages from database
    message_data = message_service.retrieve_messages(jsonify=True)
    if not message_data and not isinstance(message_data, list):
        logger.error("Failed to display messages.")
        return render_template("error.html", message="Failed to display messages.")

    logger.debug("%s messages retrieved from collection 'messages'.", len(message_data))

    user_data = user_service.get_user_by_id(user_id)
    if not user_data:
        logger.error("Unable to load user info.")
        return render_template(
            "error.html",
            message="Unable to process info about your identity. Pleasy try later.",
        )

    logger.debug("Info about user retrieved successfully: %s", user_data)

    return render_template(
        "index.html",
        msg_data=message_data,
        usr_data=user_data.to_json(),
        web_name=WEBSITE_NAME,
    )


# Registration page route
@views_bp.route("/register", methods=["GET", "POST"])
def register():
    """Registration page"""

    log_request()

    # Signup form handle
    form = RegForm(request.form)

    if request.method != "POST":
        return render_template("register.html", form=form)

    # Here goes validating of WTForm inputs
    if not form.validate():
        logger.debug("Validation of registration form's input failed")
        return render_template("register.html", form=form)

    # If everything's ok, retrieve inputs from form
    username = form.username.data
    email = form.email.data
    password = form.password.data

    # Check whether user tries to register with used credentials
    if user_service.get_user_info(username=username) or user_service.get_user_info(
        email=email
    ):
        flash("These credentials are already in use.")
        return redirect(request.url)

    # Make sure insertion is completed without errors
    result = user_service.insert_user(username, password, email)
    if not result:
        logger.error("New user registration failed")
        return render_template(
            "error.html",
            message="Registration failed due to the yet unknown reasons. Try again later.",
        )

    logger.info("New user registration is completed successfully")

    return redirect("/login")


# Login page route
@views_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""

    log_request()

    # Login form handle
    form = LogForm(request.form)

    if request.method != "POST":
        return render_template("login.html", form=form)

    if not form.validate():
        logger.debug("Validation of registration form's input failed")
        return render_template("login.html", form=form)

    username = form.username.data
    password = form.password.data

    # Check whether user exists in the database
    if not user_service.get_user_info(username=username):
        flash("Invalid username or password.")
        return render_template("login.html", form=form)

    [user_data] = user_service.get_user_info(username=username)
    # Here we validate whether user exists or if password for user is valid
    if not user_data or not user_data.verify_password(password):
        flash("Invalid username or password.")
        logger.info("Login failed")
        return render_template("login.html", form=form)

    # Creating session token for user, considering it as successful login,
    # redirecting to main page
    response = redirect("/")
    access_token = create_access_token(identity=str(user_data.user_id))
    set_access_cookies(response, access_token)

    logger.info("Login successful.")

    return response


@views_bp.route("/logout")
@jwt_required()
def logout():
    """Logout function"""

    log_request()
    response = redirect("/login")
    unset_jwt_cookies(response)

    logger.info("User logged out")

    return response


@views_bp.route("/myprofile", methods=["GET", "POST"])
@jwt_required()
def profile():
    """Display profile page"""

    log_request()

    user_id = get_jwt_identity()

    # Retrieve info from database about user
    user_data = user_service.get_user_by_id(user_id)
    if not user_data:
        logger.error("Unable to load user info.")
        return render_template(
            "error.html",
            message="Unable to process info about your identity. Pleasy try later.",
        )

    user_data = user_data.to_json()
    current_user = user_data.get("username")
    logger.debug("Current user: %s", current_user)

    # Get csrf token to put in rendered form
    csrf_token = request.cookies.get("csrf_access_token")

    # Edit profile form handle
    form = EditProfileForm(request.form)

    if request.method != "POST":

        # Placeholder values from database to display in profile
        for field in form:
            if field.name == "csrf_token":
                logger.debug("CSRF token is set")
                field.data = csrf_token
            elif user_data.get(field.name):
                field.data = user_data.get(field.name)
            # If the field from user's document is empty
            else:
                field.data = ""

        return render_template(
            "profile.html",
            form=form,
            current_user=current_user,
            csrf_token=csrf_token,
            data=user_data,
            web_name=WEBSITE_NAME,
        )

    # Check if request contains data about file uploaded
    content_clean = request.files["file"].read()
    if content_clean != b"":

        # Verify received image content
        if not verify_image(content_clean):
            flash("The file is inappropriate or corrupted. Try again")
            return redirect(request.url)

        # Generate new random name for file that will be stored
        picture_name = random_strings_generator()

        # Saving file to it's defined path
        with open(
            os.path.join(PROFILE_PICTURE_STORAGE_PATH, picture_name), "wb"
        ) as file:
            file.write(content_clean)

        # Update profile picture filename in database
        result = user_service.update_user(user_id, profile_picture=picture_name)
        if not result:
            logger.debug("Profile picture update failed.")
            flash("Unable to renew your profile picture. Try again later.")
            return redirect(request.url)

        # remove old picture to avoid trashing
        if user_data.get("profile_picture") is not None:
            try:
                os.remove(
                    os.path.join(PROFILE_PICTURE_STORAGE_PATH, user_data.get("profile_picture"))
                )
                logger.debug("Previous picture is removed.")
            except FileNotFoundError:
                logger.debug("No picture to remove: proceeding...")

        return render_template(
            "profile.html",
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
            # If the field from user's document is empty
            else:
                field.data = ""

        return render_template(
            "profile.html",
            form=form,
            current_user=current_user,
            csrf_token=csrf_token,
            data=user_data,
        )

    # Create dictionary for values that were changed
    newvalues = {}

    for field in form:

        # Exclude hidden csrf_token field or other inappropriate fields
        if field.name not in ["username", "password", "email", "bio"]:
            continue

        # Check if provided data is the same as previous
        if field.data == user_data[field.name]:
            continue

        # Check fields that may be repeatable
        if field.name not in ["username", "email"]:
            newvalues[field.name] = field.data
            continue

        kwargs = {field.name: field.data}

        # Check whether user tries to replace username/email with used credentials
        if user_service.get_user_info(**kwargs):
            flash("These credentials are already in use.")

            return redirect(request.url)

        newvalues[field.name] = field.data

    # Check whether the values need to be updated
    if len(newvalues) > 0:
        logger.debug("Values to update: %s", len(newvalues))

        result = user_service.update_user(user_id, update_dict=newvalues)
        if not result:
            logger.debug("Data update failed")
            return render_template(
                "error.html", message="Unable to renew your info. Try again later."
            )

        logger.info("User info updated successfully")

    return redirect(request.url)


@views_bp.route("/profile/<user>", methods=["GET"])
@jwt_required()
def public_profile(user):
    """Display profile page in public mode"""

    log_request()

    user_id = get_jwt_identity()
    current_user_info = user_service.get_user_by_id(user_id)
    if not current_user_info:
        logger.error("Unable to load user info.")
        return render_template(
            "error.html",
            message="Unable to process info about your identity. Pleasy try later.",
        )

    current_user = current_user_info.username
    logger.debug("Current user: %s", current_user)

    # Check whether user exists. If not, throw 404
    if not user_service.get_user_info(username=user):
        logger.debug("The username profile that was tried to access does not exist")
        return abort(404)

    logger.debug("Info about user retrieved successfully")
    user_data = user_service.get_user_info(username=user)[0].to_json()

    return render_template(
        "profile_public.html",
        current_user=current_user,
        data=user_data,
        web_name=WEBSITE_NAME,
    )


@views_bp.route("/profile-picture/<user>", methods=["GET"])
@jwt_required()
def profile_picture(user):
    """Retrieve users' profile pictures"""

    log_request()

    user_info = user_service.get_user_info(username=user)
    if not user_info:
        logger.error("Unable to load user info.")
        return render_template(
            "error.html",
            message="Unable to process info about your identity. Pleasy try later.",
        )

    profile_picture_name = user_info[0].profile_picture

    # Check if user has his profile picture set -
    # if not - return path with default picture
    if profile_picture_name is None:
        logger.debug("Profile picture not set: using default.")
        return send_file(DEFAULT_PROFILE_PICTURE_PATH)

    profile_picture_path = os.path.join(PROFILE_PICTURE_STORAGE_PATH, profile_picture_name)

    if not os.path.exists(profile_picture_path):
        logger.debug("Profile picture not found: using default.")
        return send_file(DEFAULT_PROFILE_PICTURE_PATH)

    return send_file(profile_picture_path)


@views_bp.route("/manage")
@privilege_required
def manage_chat():
    """Page to handle chat settings"""

    log_request()

    return "Welcome to admin panel! Under maintainance. Stand by"
