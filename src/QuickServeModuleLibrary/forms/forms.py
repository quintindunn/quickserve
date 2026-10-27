from typing import TYPE_CHECKING
from markupsafe import Markup
from QuickServeModuleLibrary.forms.datatypes import SubmitButton

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
        firstName = String(default="Quintin", placeholder="First Name", required=True)
        lastName = String(default="", placeholder="Last Name", required=False)
        isAdmin = Checkbox(default=True, required=True, label="Is Admin")
        userColor = Color(default="#00ff00", required=True, label="User Color")
        textColor = Color(default=(255, 0, 0), required=True, label="User Color")
        userEmail = Email(
            placeholder="dunnquintin07@gmail.com", required=False, label="User Email"
        )
        userPic = File(accept="image/*", label="Profile Picture")
        age = Number(placeholder="Age", label="User Age", min=18, max=100)
        password = Password(
            placeholder="Password123$",
            minlength=8,
            maxlength=32,
            pattern=r"[a-ZA-Z0-9]",
        )
        userType = RadioSelector("developer", ["developer", "user"])
        rating = Range(9, max=10, min=1, label="How Good Is This Form")

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
