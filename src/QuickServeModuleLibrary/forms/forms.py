from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServeModuleLibrary.forms.datatypes import *


class QSForm:
    @staticmethod
    def _generate_form_head():
        return f"<form>"

    @staticmethod
    def _generate_form_foot():
        return f"</form>"

    def compile(self, with_submit: bool = True):
        attr_names = filter(lambda x: not x.startswith("_"), self.__class__.__dict__)

        attr_dict: dict[str, BaseDataType] = {
            k: getattr(self.__class__, k) for k in attr_names
        }

        inputs = [self._generate_form_head()]
        for k, v in attr_dict.items():
            inputs.append(v.compile(id=k))

        if with_submit:
            inputs.append(SubmitButton(default="Submit", label="").compile("submit"))
        inputs.append(self._generate_form_foot())

        return Markup("\n".join(inputs))


if __name__ == "__main__":
    from QuickServeModuleLibrary.forms.datatypes import *


    class SampleForm(QSForm):
        firstName = String(
            default="Quintin",
            placeholder="First Name",
            required=True,
        )
        lastName = String(
            default="",
            placeholder="Last Name",
        )
        isAdmin = Checkbox(
            default=True,
            required=True,
            label="Is Admin",
        )
        userColor = Color(
            default="#00ff00",
            required=True,
            label="User Color",
        )
        textColor = Color(
            default=(255, 0, 0),
            required=True,
            label="Text Color",
        )
        userEmail = Email(
            placeholder="dunnquintin07@gmail.com",
            label="User Email",
        )
        userPic = File(
            accept="image/*",
            label="Profile Picture",
        )
        age = Number(
            placeholder="Age",
            label="User Age",
            min=18,
            max=100,
            step=1,
        )
        password = Password(
            placeholder="Password123$",
            minlength=8,
            maxlength=32,
            pattern=r"[a-zA-Z0-9]+",
        )
        userType = RadioSelector(
            default="developer",
            options=["developer", "user"],
            label="User Type",
            required=True,
        )
        rating = Range(
            default=9,
            min=1,
            max=10,
            step=1,
            label="How Good Is This Form",
        )
        githubUrl = URL(
            placeholder="GitHub URL",
            required=True,
        )
        accountExpiration = Time(
            default=datetime.time(12, 0),
            min=datetime.time(2, 30),
            max=datetime.time(22, 30),
            step=30,
            label="Account Expiration",
        )
        bio = Textarea(
            default="I Like Trains",
            placeholder="Enter your bio",
            rows=5,
            cols=40,
            maxlength=500,
            required=True,
        )
        createdAt = DateTime(
            default=datetime.datetime(2026, 10, 27, 14, 30),
            min=datetime.datetime(2026, 10, 27, 0, 0),
            required=True,
            label="Created At",
            step=1,
        )
        resetForm = Reset(label="Clear")

    from flask import Flask

    app = Flask(__name__)

    @app.route("/")
    def index():
        form = SampleForm()
        form_html = form.compile()
        print(form_html)
        css = """
        <style>
        body, body > * {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        form > * {
            margin-top: 1vh;
        }
        </style>
        """
        return f"<html><head>{css}</head><body>{form_html}</body></html>"

    app.run(host="0.0.0.0", port=8085, debug=True)
