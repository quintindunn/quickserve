from flask import url_for, request

from QuickServeModuleLibrary.forms.datatypes import SubmitButton, BaseDataType, Hidden
from markupsafe import Markup


class QSForm:
    instance_uuid: Hidden

    def _generate_form_head(self):
        if not hasattr(request, "module"):
            return f'<form class="qs-form" action="" method="POST">'
        module_name: str = getattr(request, "module")
        action_url = url_for(
            "modules.action", module_name=module_name, method=self._action_name
        )
        return f'<form class="qs-form" action="{action_url}" method="POST">'

    @staticmethod
    def _generate_form_foot():
        return f"</form>"

    def __init__(self, action_name: str, instance_uuid: str):
        self._action_name = action_name
        self._instance_uuid = instance_uuid

    def compile(self, submit_text: str = "submit", with_submit: bool = True):
        attr_names = filter(lambda x: not x.startswith("_"), self.__class__.__dict__)

        attr_dict: dict[str, BaseDataType] = {
            k: getattr(self.__class__, k) for k in attr_names
        }

        inputs = [self._generate_form_head()]
        for k, v in attr_dict.items():
            inputs.append(v.compile(id=k))
        inputs.append(Hidden(value=self._instance_uuid).compile("instance-uuid"))

        if with_submit:
            inputs.append(SubmitButton(default="Submit", label="", inner_text=submit_text).compile("submit"))
        inputs.append(self._generate_form_foot())

        return Markup("\n".join(inputs))

    @classmethod
    def response_from_request(cls, request_kwargs: dict):
        instance = cls.__new__(cls)

        if "instance-uuid" in request_kwargs:
            instance.instance_uuid = Hidden()
            instance.instance_uuid.response = request_kwargs["instance-uuid"]

        for attr_name in cls.__dict__:
            if attr_name.startswith("_"):
                continue

            if attr_name in request_kwargs:
                parent = getattr(instance, attr_name)
                setattr(parent, "response", request_kwargs[attr_name])
            else:
                setattr(instance, attr_name, None)

        return instance
