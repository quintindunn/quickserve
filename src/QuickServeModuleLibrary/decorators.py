import dataclasses
from typing import Callable

from functools import wraps as _wraps
from flask import request as _request


@dataclasses.dataclass
class RegisteredPage:
    page_name: str
    instance_specific: bool


def page(
    func: Callable | None = None,
    page_name: str | None = None,
    instance_specific: bool = False,
) -> Callable:
    """
    Registers a page within a module.

    :param func: The function to decorate.
    :param page_name: The name of the page.
    :param instance_specific: Whether the page can only be viewed in an instance.
    :return: The decorated function.
    """

    def decorator(func: Callable) -> Callable:
        @_wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, "QS_INTERNAL_REGISTERED_PAGES"):
                self.QS_INTERNAL_REGISTERED_PAGES = []

            name = page_name if page_name is not None else func.__name__

            registered_page = RegisteredPage(name, instance_specific)
            self.QS_INTERNAL_REGISTERED_PAGES.append(registered_page)

            if instance_specific:
                if not hasattr(_request, "instance"):
                    return (
                        "<!DOCTYPE HTML>"
                        "<html><head><title>404 Not Found!</title></head>"
                        "<body><h1>Page not found!</h1></body></html>"
                    )

                instance = getattr(_request, "instance")
                return func(self, instance, *args, **kwargs)

            return func(self, *args, **kwargs)

        return wrapper

    if func is not None:
        return decorator(func)

    return decorator
