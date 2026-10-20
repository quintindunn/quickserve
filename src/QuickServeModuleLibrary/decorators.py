import dataclasses
from collections.abc import Callable
from functools import wraps as _wraps

from flask import request as _request


@dataclasses.dataclass
class RegisteredPage:
    page_name: str
    instance_specific: bool


class Page:
    def __init__(
        self,
        func: Callable,
        page_name: str | None = None,
        instance_specific: bool = False,
        module: object | None = None,
    ) -> None:
        """
        Initializes a page.

        :param func: The original decorated function.
        :param page_name: The name used to register the page. Defaults to the function name.
        :param instance_specific: Whether the page requires a BaseInstance.
        :param module: The module instance this page belongs to.
        """
        self.func = func
        self.page_name = page_name or func.__name__
        self.instance_specific = instance_specific
        self.module = module

    def __call__(self, *args, **kwargs):
        """
        Executes the page function.

        :param args: args passed to the function.
        :param kwargs: kwargs passed to the function.
        :return: The result returned by the page function.
        """
        if self.module is None:
            raise RuntimeError(f"Page '{self.page_name}' is not bound to a module.")

        if self.instance_specific:
            if not hasattr(_request, "instance"):
                return (
                    "<!DOCTYPE HTML>"
                    "<html><head><title>404 Not Found!</title></head>"
                    "<body><h1>Page not found!</h1></body></html>"
                )

            return self.func(
                self.module,
                _request.instance,  # noqa
                *args,
                **kwargs,
            )

        return self.func(self.module, *args, **kwargs)


class PageDefinition:

    def __init__(
        self,
        func: Callable,
        page_name: str | None = None,
        instance_specific: bool = False,
    ) -> None:
        self.func = func
        self.page_name = page_name or func.__name__
        self.instance_specific = instance_specific

    def __set_name__(self, owner: type, name: str) -> None:
        """
        Wraps the class initializer to register decorated pages.

        :param owner: The class containing this descriptor.
        :param name: The attribute name assigned to this descriptor.
        :return: None.
        """
        if owner.__dict__.get("_QS_PAGE_INIT_WRAPPED", False):
            return

        original_init = owner.__init__

        @_wraps(original_init)
        def init_with_pages(self, *args, **kwargs) -> None:
            original_init(self, *args, **kwargs)

            registry: dict[str, Page] = {}

            for cls in reversed(type(self).__mro__):
                for attr_name, attr in cls.__dict__.items():
                    if isinstance(attr, PageDefinition):
                        registry[attr.page_name] = Page(
                            attr.func,
                            page_name=attr.page_name,
                            instance_specific=attr.instance_specific,
                            module=self,
                        )

            self.QS_INTERNAL_REGISTERED_PAGES = registry

        owner.__init__ = init_with_pages
        owner._QS_PAGE_INIT_WRAPPED = True

    def __get__(self, instance: object | None, owner: type | None = None):
        """
        Returns the descriptor or a callable bound to the module instance.

        :param instance: The module instance accessing the method, or None for class access.
        :param owner: The class containing the descriptor.
        :return: The descriptor on class access, or the bound method on instance access.
        """
        if instance is None:
            return self

        @_wraps(self.func)
        def wrapper(*args, **kwargs):
            if self.instance_specific:
                if not hasattr(_request, "instance"):
                    return (
                        "<!DOCTYPE HTML>"
                        "<html><head><title>404 Not Found!</title></head>"
                        "<body><h1>Page not found!</h1></body></html>"
                    )

                return self.func(
                    instance,
                    _request.instance,
                    *args,
                    **kwargs,
                )

            return self.func(instance, *args, **kwargs)

        return wrapper


def page(
    func: Callable | None = None,
    *,
    page_name: str | None = None,
    instance_specific: bool = False,
) -> PageDefinition | Callable:
    """
    Registers a page within a module.

    :param func: The function being decorated, when using @page directly.
    :param page_name: The registered page name, defaults to the function name.
    :param instance_specific: Whether the page requires a BaseInstance.
    :return: The page definition or a decorator that creates one.
    """

    def decorator(fn: Callable) -> PageDefinition:
        return PageDefinition(
            fn,
            page_name=page_name,
            instance_specific=instance_specific,
        )

    if func is not None:
        return decorator(func)

    return decorator
