import logging
import re
from typing import Any

from markupsafe import Markup, escape


logger = logging.getLogger(__name__)

_ATTRIBUTE_NAME_PATTERN = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_.:-]*$")

_BOOLEAN_ATTRIBUTES = {
    "allowfullscreen",
    "async",
    "autofocus",
    "autoplay",
    "checked",
    "controls",
    "default",
    "defer",
    "disabled",
    "formnovalidate",
    "hidden",
    "inert",
    "ismap",
    "itemscope",
    "loop",
    "multiple",
    "muted",
    "nomodule",
    "novalidate",
    "open",
    "playsinline",
    "readonly",
    "required",
    "reversed",
    "selected",
}


def _compile_if_callable(value: Any) -> Any:
    return value() if callable(value) else value


def _compile_if_callable_always_escape(value: Any) -> Markup:
    return escape(_compile_if_callable(value))


def _generate_label(original: str) -> str:
    original = original.replace("_", " ")

    if original.upper() == original:
        return original.title()

    words = re.findall(
        r"[A-Z]+(?=[A-Z][a-z]|\b)|[A-Z]?[a-z]+|[A-Z]+|\d+",
        original,
    )

    return " ".join(words).title()


def _build_attrs(attrs: dict[str, Any]) -> str:
    output = []

    for key, value in attrs.items():
        if value is None or value is False:
            continue

        if not isinstance(key, str) or not _ATTRIBUTE_NAME_PATTERN.fullmatch(key):
            logger.warning(
                "Cannot handle HTML attribute {%s: %s}",
                repr(key),
                repr(value),
            )
            continue

        value = _compile_if_callable(value)

        if value is None or value is False:
            continue

        if key.lower() in _BOOLEAN_ATTRIBUTES:
            if value is True:
                output.append(f" {key}")
            elif value:
                output.append(f" {key}")
            continue

        if value is True:
            output.append(f" {key}")
            continue

        output.append(f' {key}="{escape(value)}"')

    return "".join(output)


def _build_element(
    tag: str,
    attrs: dict[str, Any],
    content: Any = None,
) -> Markup:
    output = f"<{tag}{_build_attrs(attrs)}>"

    if content is not None:
        content = _compile_if_callable(content)
        output += str(content if isinstance(content, Markup) else escape(content))

    output += f"</{tag}>"

    return Markup(output)


def build_input(
    input_type: str | None = None,
    id: str | None = None,
    name: str | None = None,
    value: Any = None,
    required: bool | None = None,
    **other,
) -> Markup:
    attrs = {
        "type": input_type,
        "id": id,
        "name": id if name is None else name,
        "value": value,
        "required": required,
        **other,
    }

    return Markup(f"<input{_build_attrs(attrs)}>")


def build_button(
    button_type: str | None = None,
    id: str | None = None,
    value: Any = None,
    name: str | None = None,
    content: Any = None,
    **other,
) -> Markup:
    attrs = {
        "type": button_type,
        "id": id,
        "name": id if name is None else name,
        "value": value,
        **other,
    }

    return _build_element("button", attrs, content)


def build_input_with_label(
    label: str | None,
    input_type: str | None = None,
    id: str | None = None,
    name: str | None = None,
    value: Any = None,
    required: bool | None = None,
    **other,
) -> Markup:
    return Markup(
        f"<label>{escape(label or '')}"
        f"{build_input(input_type, id, name, value, required, **other)}"
        f"</label>"
    )


def build_button_with_label(
    label: str | None,
    button_type: str | None = None,
    id: str | None = None,
    name: str | None = None,
    value: Any = None,
    inner_text: Any = None,
    **other,
) -> Markup:
    button = build_button(
        button_type=button_type,
        id=id,
        name=name,
        value=value,
        content=inner_text,
        **other,
    )

    return Markup(f"<label>{escape(label or '')}{button}</label>")
