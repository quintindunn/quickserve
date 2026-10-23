import logging
from typing import Any
from markupsafe import Markup

from QuickServeModuleLibrary.forms.util import (
    build_input_with_label,
    build_button_with_label,
    _generate_label,
)

logger = logging.getLogger(__name__)


class BaseDataType:
    def __init__(
        self,
        default: Any = None,
        required: bool = False,
        label: str | None = None,
    ):
        self.default: Any = default
        self.required: bool = required
        self.label: str | None = label

    def compile(self, id: str) -> Markup:
        raise NotImplementedError


class BaseInput(BaseDataType):
    def __init__(
        self,
        input_type: str,
        default: Any = None,
        *,
        placeholder: str | None = None,
        required: bool = False,
        label: str | None = None,
        **other,
    ):
        super().__init__(default, required, label)
        self.input_type = input_type
        self.placeholder = placeholder
        self.other = other

    def compile(self, id: str) -> Markup:
        fallback_label = self.label if self.label is not None else _generate_label(id)

        return build_input_with_label(
            fallback_label,
            self.input_type,
            id,
            self.default,
            self.required,
            placeholder=self.placeholder,
            **self.other,
        )


class String(BaseInput):
    def __init__(
        self,
        default: str | None = None,
        *,
        placeholder: str | None = None,
        required: bool = False,
        label: str | None = None,
    ):
        super().__init__(
            "text",
            default,
            placeholder=placeholder,
            required=required,
            label=label,
        )


class Checkbox(BaseInput):
    def __init__(
        self,
        default: bool = False,
        *,
        required: bool = False,
        label: str | None = None,
    ):
        super().__init__(
            "checkbox",
            default=None,
            required=required,
            checked=default,
            label=label,
        )


class Color(BaseInput):
    def __init__(
        self,
        default: str | tuple[int, int, int] = (0, 0, 0),
        *,
        required: bool = False,
        label: str | None = None,
    ):
        if isinstance(default, tuple):
            default = f"#{default[0]:02x}{default[1]:02x}{default[2]:02x}"
        super().__init__(
            "color",
            default=default,
            required=required,
            label=label,
        )


class Email(BaseInput):
    def __init__(
        self,
        default: str | None = None,
        *,
        placeholder: str | None = None,
        required: bool = False,
        label: str | None = None,
        multiple: bool = False,
    ):
        super().__init__(
            "email",
            default=default,
            placeholder=placeholder,
            required=required,
            label=label,
            multiple=multiple
        )


class File(BaseInput):
    def __init__(
        self,
        default: str | None = None,
        *,
        accept: str | None = None,
        required: bool = False,
        label: str | None = None,
        multiple: bool = False,
    ):
        super().__init__(
            "file",
            default=default,
            required=required,
            multiple=multiple,
            accept=accept,
            label=label,
        )


class Number(BaseInput):
    def __init__(
        self,
        default: str | None = None,
        *,
        min: int | None = None,
        max: int | None = None,
        required: bool = False,
        label: str | None = None,
        placeholder: str | None = None,
    ):
        super().__init__(
            "number",
            default=default,
            required=required,
            min=min,
            max=max,
            label=label,
            placeholder=placeholder
        )


class BaseButton(BaseDataType):
    def __init__(
        self,
        default: Any = None,
        *,
        button_type: str = "button",
        required: bool = False,
        label: str | None = None,
        **other,
    ):
        super().__init__(default, required, label)
        self.button_type = button_type
        self.other = other

    def compile(self, id: str) -> Markup:
        fallback_label = self.label if self.label is not None else _generate_label(id)

        return build_button_with_label(
            fallback_label,
            self.button_type,
            id,
            self.default,
            **self.other,
        )


class Button(BaseButton):
    def __init__(
        self,
        default: Any = None,
        *,
        required: bool = False,
        label: str | None = None,
        **other,
    ):
        super().__init__(
            default,
            button_type="button",
            required=required,
            label=label,
            **other,
        )


class SubmitButton(BaseButton):
    def __init__(
        self,
        default: Any = None,
        *,
        required: bool = False,
        label: str | None = None,
        **other,
    ):
        super().__init__(
            default,
            button_type="submit",
            required=required,
            label=label,
            **other,
        )
