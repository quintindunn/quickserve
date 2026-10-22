from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServeModuleLibrary.forms.datatypes import *


class QSForm:
    def _generate_form_head(self):
        return f"<form>"

    def _generate_form_foot(self):
        return f"</form>"

    def compile(self):
        attr_names = filter(lambda x: not x.startswith("_"), self.__class__.__dict__)

        attr_dict: dict[str, BaseDataType] = {
            k: getattr(self.__class__, k) for k in attr_names
        }

        inputs = [self._generate_form_head()]
        for k, v in attr_dict.items():
            inputs.append(v.compile(id=k))
        inputs.append(self._generate_form_foot())

        return "\n".join(inputs)


if __name__ == "__main__":
    from QuickServeModuleLibrary.forms.datatypes import *

    class SampleForm(QSForm):
        firstName = String(default="Quintin", placeholder="First Name", required=True)
        lastName = String(default="", placeholder="Last Name", required=False)

    form = SampleForm()
    print(form.compile())
