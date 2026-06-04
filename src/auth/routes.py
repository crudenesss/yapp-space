"""Authentication routes"""

import logging
from flask import Blueprint, flash, redirect, render_template, request
from flask.views import MethodView
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies, jwt_required

from auth.services import UserService
from auth.forms import RegForm, LogForm
from core.utils.helpers import log_request

auth_bp = Blueprint("auth", __name__)

logger = logging.getLogger("gunicorn.access")
user_service = UserService()


class RegisterView(MethodView):

    def get(self):
        log_request()
        return render_template("auth/register.html", form=RegForm(request.form))

    def post(self):
        log_request()
        form = RegForm(request.form)

        if not form.validate():
            logger.debug("Validation of registration form's input failed")
            return render_template("auth/register.html", form=form)

        username = form.username.data
        email = form.email.data
        password = form.password.data

        if user_service.get_user_info(username=username) or user_service.get_user_info(email=email):
            flash("These credentials are already in use.")
            return redirect(request.url)

        result = user_service.insert_user(username, password, email)
        if not result:
            logger.error("New user registration failed")
            return render_template(
                "errors/error.html",
                message="Registration failed due to the yet unknown reasons. Try again later.",
            )

        logger.info("New user registration is completed successfully")
        return redirect("/login")


class LoginView(MethodView):

    def get(self):
        log_request()
        return render_template("auth/login.html", form=LogForm(request.form))

    def post(self):
        log_request()
        form = LogForm(request.form)

        if not form.validate():
            logger.debug("Validation of login form's input failed")
            return render_template("auth/login.html", form=form)

        username = form.username.data
        password = form.password.data

        user_list = user_service.get_user_info(username=username)
        user_data = user_list[0] if user_list else None

        if not user_data or not user_data.verify_password(password):
            flash("Invalid username or password.")
            logger.info("Login failed")
            return render_template("auth/login.html", form=form)

        response = redirect("/")
        access_token = create_access_token(identity=str(user_data.user_id))
        set_access_cookies(response, access_token)

        logger.info("Login successful.")
        return response


class LogoutView(MethodView):
    decorators = [jwt_required()]

    def get(self):
        log_request()
        response = redirect("/login")
        unset_jwt_cookies(response)
        logger.info("User logged out")
        return response


auth_bp.add_url_rule(
    "/register",
    view_func=RegisterView.as_view("register"),
    methods=["GET", "POST"],
)
auth_bp.add_url_rule(
    "/login",
    view_func=LoginView.as_view("login"),
    methods=["GET", "POST"],
)
auth_bp.add_url_rule(
    "/logout",
    view_func=LogoutView.as_view("logout"),
    methods=["GET"],
)
