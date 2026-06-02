"""WTforms used in application"""

from wtforms import (
    Form,
    StringField,
    PasswordField,
    validators,
    TextAreaField,
    HiddenField,
)
from utils.constants import WEBSITE_NAME


class RegForm(Form):
    """Form to sign up to the app

    Args:
        Form (class): Form base class
    """

    username = StringField(
        "Username",
        [
            validators.DataRequired(),
            validators.Length(
                min=5, max=32, message="Username must contain between 5 and 32 symbols"
            ),
            validators.Regexp(
                "^[a-zA-Z0-9_]+$",
                message="Username must only contain Latin letters, numbers or underscores",
            ),
        ],
        description=f"""Username is your unique name in {WEBSITE_NAME}.
            You can use Latin letters (both cases), numbers and underscores. 
            Length must be 5-32 symbols.""",
    )
    email = StringField(
        "E-mail",
        [validators.DataRequired(), validators.Email(message="Invalid email format.")],
    )
    password = PasswordField(
        "New Password",
        [
            validators.InputRequired(),
            validators.EqualTo("confirm", message="Passwords must match"),
            validators.Length(
                min=8,
                max=128,
                message="Password must contain between 8 and 128 symbols",
            ),
        ],
    )
    confirm = PasswordField("Repeat Password", [validators.InputRequired()])


class LogForm(Form):
    """Form to log in the app"""

    username = StringField("Username", [validators.InputRequired()])
    password = PasswordField("Password", [validators.InputRequired()])


class EditProfileForm(Form):
    """Form to fast-edit info about user"""

    csrf_token = HiddenField("Hidden", name="csrf_token")
    username = StringField(
        "Username",
        [
            validators.DataRequired(),
            validators.Length(
                min=5, max=32, message="Username must contain between 5 and 32 symbols"
            ),
            validators.Regexp("^[a-zA-Z0-9_]+$"),
        ],
        description=f"""Username is your unique name in {WEBSITE_NAME}.
            You can use Latin letters (both cases), numbers and underscores. 
            Length must be 5-32 symbols.""",
        render_kw={"class": "editable", "readonly": True},
        name="username",
    )
    email = StringField(
        "E-mail",
        [validators.DataRequired(), validators.Email(message="Invalid email format.")],
        render_kw={"class": "editable", "readonly": True},
        name="email",
    )
    bio = TextAreaField(
        "Bio",
        [validators.Length(max=256, message="The maximum of 256 symbols are allowed")],
        render_kw={"class": "editable", "readonly": True},
        name="bio",
    )
