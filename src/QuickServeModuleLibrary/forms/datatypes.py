import datetime
import logging
from typing import Any

from markupsafe import Markup, escape

from QuickServeModuleLibrary.forms.util import (
    build_input_with_label,
    build_button_with_label,
    build_input,
    _build_attrs,
    _generate_label,
)


logger = logging.getLogger(__name__)


def _format_default(value: Any) -> Any:
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()

    return value


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

    def compile(self, id: str, name: str | None = None) -> Markup:
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

    def compile(
        self, id: str, name: str | None = None, use_label: bool = True
    ) -> Markup:
        fallback_label = self.label if self.label is not None else _generate_label(id)
        value = None if self.input_type == "file" else _format_default(self.default)

        attrs = {
            "input_type": self.input_type,
            "id": id,
            "name": id if name is None else name,
            "value": value,
            "required": self.required,
            "placeholder": self.placeholder,
            **self.other,
        }

        if use_label:
            return build_input_with_label(
                label=fallback_label,
                **attrs,
            )

        return build_input(**attrs)


class String(BaseInput):
    def __init__(
        self,
        default: str | None = None,
        *,
        placeholder: str | None = None,
        required: bool = False,
        label: str | None = None,
        minlength: int | None = None,
        maxlength: int | None = None,
        pattern: str | None = None,
    ):
        super().__init__(
            "text",
            default,
            placeholder=placeholder,
            required=required,
            label=label,
            minlength=minlength,
            maxlength=maxlength,
            pattern=pattern,
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
            required=required,
            label=label,
            checked=default,
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
            if len(default) != 3 or any(
                not isinstance(channel, int) or not 0 <= channel <= 255
                for channel in default
            ):
                raise ValueError("Color must be an RGB tuple with values from 0 to 255")

            default = "#{:02x}{:02x}{:02x}".format(*default)

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
            multiple=multiple,
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
        default: int | float | str | None = None,
        *,
        min: int | float | None = None,
        max: int | float | None = None,
        step: int | float | None = None,
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
            step=step,
            label=label,
            placeholder=placeholder,
        )


class Password(BaseInput):
    def __init__(
        self,
        default: str | None = None,
        *,
        required: bool = False,
        label: str | None = None,
        placeholder: str | None = None,
        minlength: int | None = None,
        maxlength: int | None = None,
        pattern: str | None = None,
    ):
        super().__init__(
            "password",
            default=default,
            required=required,
            label=label,
            placeholder=placeholder,
            minlength=minlength,
            maxlength=maxlength,
            pattern=pattern,
        )


class Radio(BaseInput):
    def __init__(
        self,
        value: str,
        *,
        required: bool = False,
        label: str | None = None,
        selected: bool = False,
    ):
        super().__init__(
            "radio",
            default=value,
            required=required,
            label=label,
            checked=selected,
        )


class RadioSelector(BaseDataType):
    def __init__(
        self,
        default: str | None = None,
        options: list[str] | None = None,
        *,
        label: str | None = None,
        required: bool = False,
    ):
        super().__init__(default, required, label)

        self._radios = [
            Radio(
                value,
                selected=value == default,
                required=required,
                label=value,
            )
            for value in (options or [])
        ]

    def compile(self, id: str, name: str | None = None) -> Markup:
        fallback_label = self.label if self.label is not None else _generate_label(id)
        field_name = id if name is None else name
        radios = []

        for index, radio in enumerate(self._radios):
            radio_id = f"{id}_{index}"
            input_html = radio.compile(
                id=radio_id,
                name=field_name,
                use_label=False,
            )

            radio_label = radio.label or _generate_label(radio_id)
            radios.append(
                Markup("<label>")
                + input_html
                + escape(radio_label)
                + Markup("</label>")
            )

        return (
            Markup("<fieldset><legend>")
            + escape(fallback_label or "")
            + Markup("</legend>")
            + Markup("\n").join(radios)
            + Markup("</fieldset>")
        )


class Range(BaseInput):
    def __init__(
        self,
        default: int | float | None = None,
        *,
        min: int | float | None = None,
        max: int | float | None = None,
        step: int | float | None = None,
        required: bool = False,
        label: str | None = None,
    ):
        super().__init__(
            "range",
            default=default,
            required=required,
            min=min,
            max=max,
            step=step,
            label=label,
        )


class URL(BaseInput):
    def __init__(
        self,
        default: str | None = None,
        *,
        placeholder: str | None = None,
        required: bool = False,
        label: str | None = None,
    ):
        super().__init__(
            "url",
            default=default,
            placeholder=placeholder,
            required=required,
            label=label,
        )


class Reset(BaseInput):
    def __init__(self, label: str | None = None):
        super().__init__("reset", label=label)


class Date(BaseInput):
    def __init__(
        self,
        default: datetime.date | str | None = None,
        *,
        min: datetime.date | str | None = None,
        max: datetime.date | str | None = None,
        required: bool = False,
        label: str | None = None,
    ):
        super().__init__(
            "date",
            default=default,
            min=_format_default(min),
            max=_format_default(max),
            required=required,
            label=label,
        )


class Time(BaseInput):
    def __init__(
        self,
        default: datetime.time | str | None = None,
        *,
        min: datetime.time | str | None = None,
        max: datetime.time | str | None = None,
        step: int | None = None,
        required: bool = False,
        label: str | None = None,
    ):
        super().__init__(
            "time",
            default=default,
            min=_format_default(min),
            max=_format_default(max),
            step=step,
            required=required,
            label=label,
        )


class DateTime(BaseInput):
    def __init__(
        self,
        default: datetime.datetime | str | None = None,
        *,
        min: datetime.datetime | str | None = None,
        max: datetime.datetime | str | None = None,
        step: int | None = None,
        required: bool = False,
        label: str | None = None,
    ):
        super().__init__(
            "datetime-local",
            default=default,
            min=_format_default(min),
            max=_format_default(max),
            step=step,
            required=required,
            label=label,
        )


class BaseButton(BaseDataType):
    def __init__(
        self,
        default: Any = None,
        *,
        button_type: str = "button",
        required: bool = False,
        label: str | None = None,
        inner_text: str | None = None,
        **other,
    ):
        super().__init__(default, required, label)
        self.button_type = button_type
        self.other = other
        self.inner_text = inner_text

    def compile(self, id: str, name: str | None = None) -> Markup:
        fallback_label = self.label if self.label is not None else _generate_label(id)

        return build_button_with_label(
            label=fallback_label,
            button_type=self.button_type,
            id=id,
            name=name,
            value=self.default,
            inner_text=self.inner_text,
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
        inner_text: str | None = "Submit",
        **other,
    ):
        super().__init__(
            default,
            button_type="submit",
            required=required,
            label=label,
            inner_text=inner_text,
            **other,
        )


class Textarea(BaseDataType):
    def __init__(
        self,
        default: str | None = None,
        *,
        placeholder: str | None = None,
        required: bool = False,
        label: str | None = None,
        rows: int | None = None,
        cols: int | None = None,
        minlength: int | None = None,
        maxlength: int | None = None,
        **other,
    ):
        super().__init__(default, required, label)
        self.placeholder = placeholder
        self.rows = rows
        self.cols = cols
        self.minlength = minlength
        self.maxlength = maxlength
        self.other = other

    def compile(self, id: str, name: str | None = None) -> Markup:
        fallback_label = self.label if self.label is not None else _generate_label(id)

        attrs = {
            "id": id,
            "name": id if name is None else name,
            "placeholder": self.placeholder,
            "required": self.required,
            "rows": self.rows,
            "cols": self.cols,
            "minlength": self.minlength,
            "maxlength": self.maxlength,
            **self.other,
        }

        attrs_string = _build_attrs(attrs)

        content = self.default
        if callable(content):
            content = content()

        return Markup(
            f"<label>{escape(fallback_label or '')}"
            f"<textarea{attrs_string}>"
            f"{escape(content) if content is not None else ''}"
            f"</textarea></label>"
        )
