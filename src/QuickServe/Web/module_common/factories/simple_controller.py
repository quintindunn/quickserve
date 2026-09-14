# from typing import Callable, TYPE_CHECKING
#
# from markupsafe import Markup
#
# from QuickServe.Web import get_resource
# from QuickServeServiceLibrary.SimpleController import simple_controller_manager
#
# from flask import current_app, request
#
# if TYPE_CHECKING:
#     from QuickServe.Driver.instance.base_instance import BaseInstance
#
# def simple_controller_builder(module_name: str) -> Callable[[], str]:
#     resource: str = get_resource("simple_controller.html", mode="r")
#
#     def simple_controller():
#         assert hasattr(request, "instance")
#
#         instance: "BaseInstance" = getattr(request, "instance")
#         controller = simple_controller_manager.get_controller(port=instance.websocket_port, instance=instance)
#
#         template = current_app.jinja_env.from_string(resource)
#         context = {"module_name": module_name, "ws_url": controller.ws_url}
#         return Markup(template.render(context=context))
#
#     return simple_controller
