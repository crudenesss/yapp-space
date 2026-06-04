"""User profile forms"""

from wtforms import Form, StringField, HiddenField, TextAreaField, validators
from core.constants import WEBSITE_NAME


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
