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


def _generate_label(original: str) -> str:
    original = original.replace("_", " ")

    if original.upper() == original:
        return original.title()

    return (
        " ".join(
            re.findall(
                r"[A-Z]+(?=[A-Z][a-z]|\b)|[A-Z]?[a-z]+|[A-Z]+",
                original,
            )
        )
    ).title()


def _build_element(tag: str, attrs: dict[str, Any], content: Any = None) -> Markup:
    output = f"<{tag}"
    for key, value in attrs.items():
        if value is None or value is False:
            continue

        if not key:
            logger.warning(
                "Cannot handle attribute for %s tag {%s: %s}",
                tag,
                repr(key),
                repr(value),
            )
            continue

        if value is True:
            output += f" {key}"
        else:
            output += f' {key}="{escape(_compile_if_callable(value))}"'

    output += ">"

    if content is not None:
        output += str(escape(content) if not isinstance(content, Markup) else content)

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
        "name": name or id,
        "value": value,
        "required": required,
        **other,
    }

    output = "<input"

    for key, attr_value in attrs.items():
        if attr_value is None or attr_value is False:
            continue

        if not key:
            logger.warning(
                "Cannot handle attribute for input tag {%s: %s}",
                repr(key),
                repr(attr_value),
            )
            continue

        if attr_value is True:
            output += f" {key}"
        else:
            output += f' {key}="{escape(_compile_if_callable(attr_value))}"'

    output += ">"

    return Markup(output)


def build_button(
    button_type: str | None = None,
    id: str | None = None,
    value: Any = None,
    name: str | None = None,
    content: str | None = None,
    **other,
) -> Markup:
    return _build_element(
        "button",
        {
            "type": button_type,
            "id": id,
            "name": name or id,
            **other,
        },
        content=content,
    )


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
        f"{build_input(input_type, id, name, value, required, **other)}</label>"
    )


def build_button_with_label(
    label: str | None,
    button_type: str | None = None,
    id: str | None = None,
    name: str | None = None,
    value: Any = None,
    inner_text: str | None = None,
    **other,
) -> Markup:
    return Markup(
        f"<label>{escape(label or '')}"
        f"{build_button(button_type, id, name, value, inner_text, **other)}</label>"
    )
