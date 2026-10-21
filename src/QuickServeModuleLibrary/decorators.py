"""
Decorators for registering pages and actions

Author: Quintin Dunn
Date: 10/21/2021
"""

import dataclasses
from collections.abc import Callable
from functools import wraps as _wraps

from flask import request as _request


@dataclasses.dataclass
class RegisteredPage:
    page_name: str
    instance_specific: bool


@dataclasses.dataclass
class RegisteredAction:
    action_name: str


class RegisteredCallable:
    def __init__(
        self,
        func: Callable,
        name: str,
        module: object,
        *,
        instance_specific: bool = False,
    ) -> None:

        self.func = func
        self.name = name
        self.module = module
        self.instance_specific = instance_specific

    def __call__(self, *args, **kwargs):
        """
        Executes the registered callable.

        :param args: args passed to the function.
        :param kwargs: kwargs passed to the function.
        :return: The result returned by the function.
        """

        if self.module is None:
            raise RuntimeError(f"Callable '{self.name}' is not bound to a module.")

        if self.instance_specific:
            if not hasattr(_request, "instance") or _request.instance is None:
                return self._not_found()

            return self.func(
                self.module,
                _request.instance,  # noqa
                *args,
                **kwargs,
            )

        return self.func(self.module, *args, **kwargs)

    @staticmethod
    def _not_found():
        return (
            "<!DOCTYPE HTML>"
            "<html><head><title>404 Not Found!</title></head>"
            "<body><h1>Page not found!</h1></body></html>"
        )


class Definition:
    registry_name: str

    def __init__(
        self,
        func: Callable,
        name: str | None = None,
        *,
        instance_specific: bool = False,
    ) -> None:
        self.func = func
        self.name = name or func.__name__
        self.instance_specific = instance_specific

    def __set_name__(self, owner: type, name: str) -> None:
        """
        Wraps the class initializer to register decorated definitions.

        :param owner: The class containing the descriptor.
        :param name: The attribute name assigned to the descriptor.
        :return: None
        """

        if owner.__dict__.get("_QS_DEFINITION_INIT_WRAPPED", False):
            return

        original_init = owner.__init__

        @_wraps(original_init)
        def init_with_definitions(self, *args, **kwargs) -> None:
            original_init(self, *args, **kwargs)

            pages = {}
            actions = {}

            for cls in reversed(type(self).__mro__):
                for attr in cls.__dict__.values():
                    if isinstance(attr, PageDefinition):
                        pages[attr.name] = RegisteredCallable(
                            attr.func,
                            attr.name,
                            self,
                            instance_specific=attr.instance_specific,
                        )
                    elif isinstance(attr, ActionDefinition):
                        actions[attr.name] = RegisteredCallable(
                            attr.func,
                            attr.name,
                            self,
                        )

            self.QS_INTERNAL_REGISTERED_PAGES = pages
            self.QS_INTERNAL_REGISTERED_ACTIONS = actions

        owner.__init__ = init_with_definitions
        owner._QS_DEFINITION_INIT_WRAPPED = True

    def __get__(self, instance: object | None, owner: type | None = None):
        """
        Returns the descriptor or a callable bound to the module instance.

        :param instance: The module instance accessing the descriptor, or None for class access.
        :param owner: The class containing the descriptor.
        :return: The descriptor on class access, or the bound callable on instance access.
        """

        if instance is None:
            return self

        @_wraps(self.func)
        def wrapper(*args, **kwargs):
            if self.instance_specific:
                if not hasattr(_request, "instance"):
                    return RegisteredCallable._not_found()

                return self.func(
                    instance,
                    _request.instance,  # noqa
                    *args,
                    **kwargs,
                )

            return self.func(instance, *args, **kwargs)

        return wrapper


class PageDefinition(Definition):
    def __init__(
        self,
        func: Callable,
        page_name: str | None = None,
        instance_specific: bool = False,
    ) -> None:
        super().__init__(
            func,
            name=page_name,
            instance_specific=instance_specific,
        )


class ActionDefinition(Definition):
    def __init__(
        self,
        func: Callable,
        action_name: str | None = None,
    ) -> None:
        super().__init__(func, name=action_name)


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


def action(
    func: Callable | None = None,
    *,
    action_name: str | None = None,
) -> ActionDefinition | Callable:
    """
    Registers an action within a module.

    :param func: The function being decorated, when using @action directly.
    :param action_name: The registered action name, defaults to the function name.
    :return: The action definition or a decorator that creates one.
    """

    def decorator(fn: Callable) -> ActionDefinition:
        return ActionDefinition(
            fn,
            action_name=action_name,
        )

    if func is not None:
        return decorator(func)

    return decorator
