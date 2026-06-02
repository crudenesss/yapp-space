"""Auth forms for registration and login"""

from wtforms import Form, StringField, PasswordField, validators
from core.constants import WEBSITE_NAME


class RegForm(Form):
    """Form to sign up to the app"""

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
    """Form to log in to the app"""

    username = StringField("Username", [validators.InputRequired()])
    password = PasswordField("Password", [validators.InputRequired()])
