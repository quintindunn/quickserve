import logging
import re
from typing import Any, Callable
from markupsafe import Markup, escape


logger = logging.getLogger(__name__)


def _compile_if_callable(value: Any) -> Any:
    if isinstance(value, Callable):
        return value()
    return value


def _compile_if_callable_always_escape(value: Any) -> Any:
    return escape(_compile_if_callable(value))


def build_input(
    input_type: str | None = None,
    id: str | None = None,
    value: str | None = None,
    required: bool | None = None,
    **other
) -> Markup:
    input_type = input_type or ""
    id = id or ""
    value = value or ""
    required = required or ""

    output = "<input"
    attrs = {
        "type": escape(input_type),
        "id": escape(id),
        "value": _compile_if_callable_always_escape(value),
    }
    for k, v in attrs.items():
        if k and v:
            output += f" {k}=\"{v}\""
        elif k and not v:
            output += f" {k}"
        else:
            logger.warning("Cannot handle attribute for input tag {%s: %s}", repr(k), repr(v))

    for k, v in other.items():
        if k and v:
            output += f" {k}=\"{v}\""
        elif k and not v:
            output += f" {k}"
        else:
            logger.warning("Cannot handle attribute for input tag {%s: %s}", repr(k), repr(v))
    output += f"{' required' if required else ''}>"

    return Markup(output)


def build_input_with_label(
        label: str | None,
        input_type: str | None = None,
        id: str | None = None,
        value: str | None = None,
        required: bool | None = None,
        **other
) -> Markup:
    return Markup(f"<label>{label or ''}{build_input(input_type, id, value, required, **other)}</label>")

def _generate_label(original: str):
    original = original.replace("_", " ")
    if original.upper() == original:
        return original.title()

    return (' '.join(re.findall(r"[A-Z]+(?=[A-Z][a-z]|\b)|[A-Z]?[a-z]+|[A-Z]+", original))).title()

class BaseDataType:
    def __init__(self, default: Any, required: bool = False, label: str | None = None):
        self.default: Any = default
        self.required: bool = required
        self.label: str | None = label

    def compile(self, id: str) -> Markup:
        ...


class String(BaseDataType):
    def __init__(self, default: str, *, placeholder: str | None = None, required: bool = False, label: str | None = None):
        super().__init__(default, required, label)
        self.placeholder = placeholder

    def compile(self, id: str) -> Markup:
        fallback_label = self.label or _generate_label(id)

        return build_input_with_label(
            fallback_label,
            "text",
            id,
            self.default,
            self.required,
            placeholder=self.placeholder
        )
