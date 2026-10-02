from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServe.FileSystem.modules import BaseModule
    from QuickServe.Runtimes.runtime_manager import RuntimeManager

ABOUT_PAGE = """
{% extends "core/module.html" %}
{% block moduletitle %}
    Test Module
{% endblock %}
{% block modulehead %}
{% endblock %}
{% block modulebody %}
    <div>
        <div class="about">
            <h2>Test Module</h2>
            <p style="text-indent: 4rem">This module is for QuickServe unit testing</p>
        </div>
    </div>
{% endblock %}
"""

class Module:
    NAME: str = "Quick-Serve-Testing"
    VERSION: str = "0.0.1"
    QUICKSERVE_VERSION: str = "0.0.1"
    AUTHORS: list[dict] = [
        {"name": "Quintin Dunn", "github": "https://github.com/quintindunn"}
    ]
    PAGES: list[str] = ["about", "create", "optional_page"]

    module: "BaseModule"
    runtime_manager: "RuntimeManager"

    def __init__(self, module: "BaseModule", runtime_manager: "RuntimeManager"):
        self.module = module
        self.runtime_manager = runtime_manager

    def about(self):
        return ABOUT_PAGE

    def create(self):
        asset = self.module.get_resource_path("about.html")
        with open(asset, "r") as f:
            return f.read()

    def optional_page(self):
        asset = self.module.get_resource_path("optional_page.html")
        with open(asset, "r") as f:
            return f.read()