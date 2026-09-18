from typing import TYPE_CHECKING

from functools import wraps as _wraps
from flask import request as _request

if TYPE_CHECKING:
    from QuickServe.contracts import Service


def instance_specific(func):
    @_wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(_request, "instance"):
            return (
                "<!DOCTYPE HTML>"
                "<html><head><title>404 Not Found!</title></head>"
                "<body><h1>Page not found!</h1></body></html>"
            )
        instance = getattr(_request, "instance")
        return func(self, instance, *args, **kwargs)

    return wrapper


def simple_controller_processor(cls: "Service"):
    return cls
