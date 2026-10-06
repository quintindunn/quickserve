from typing import Tuple

from QuickServe.Application.instances import InstanceManager
from QuickServe.Common.tf_idf import TfIDF
from QuickServe.Driver.instance.base_instance import BaseInstance
from QuickServe.FileSystem.plugins import ModuleCatalog
from QuickServe.contracts import Module

from bs4 import BeautifulSoup

class Search:
    module_tfidf: TfIDF
    instance_tfidf: TfIDF
    module_registrar: set[str]

    catalog: "ModuleCatalog"
    instance_manager: "InstanceManager"

    def __init__(self, catalog: "ModuleCatalog", instance_manager: "InstanceManager"):
        self.module_tfidf = TfIDF()
        self.instance_tfidf = TfIDF()
        self.module_registrar = set()
        self.instance_registrar = set()

        self.instance_manager = instance_manager
        self.catalog = catalog

    @staticmethod
    def _build_module_tfidf_add(module: "Module") -> Tuple[str, str, str]:
        title = f"{module.NAME} {module.VERSION}"
        soup = BeautifulSoup(module.about(), features="html.parser")
        body = f"{module.DESCRIPTION}\n\n{soup.text}"
        return title, body, ""

    @staticmethod
    def _build_instance_tfidf_add(instance: "BaseInstance") -> Tuple[str, str, str]:
        title = f"{instance.instance_name} {instance.module_name} {instance.uuid}"
        return title, "", ""

    def register_module(self, module: "Module"):
        if module.NAME in self.module_registrar:
            return

        self.module_registrar.add(module.NAME)
        title, body, minor = self._build_module_tfidf_add(module)
        self.module_tfidf.add_result(identifier=module.NAME, title=title, text=body, minor=minor)

    def register_instance(self, instance: "BaseInstance"):
        if str(instance.uuid) in self.instance_registrar:
            return

        self.instance_registrar.add(str(instance.uuid))
        title, body, minor = self._build_instance_tfidf_add(instance=instance)
        self.instance_tfidf.add_result(identifier=str(instance.uuid), title=title, text=body, minor=minor)

    def update_modules(self):
        for _, module in self.catalog.items():
            self.register_module(module.module)

    def update_instances(self):
        for instance in self.instance_manager.load_all():
            self.register_instance(instance)

    def update_all(self):
        self.update_modules()
        self.update_instances()

    def search(self, query: str, max_results: int = 5):
        modules = self.module_tfidf.query(query=query, max_results=max_results)
        instances = self.instance_tfidf.query(query=query, max_results=max_results)

        return modules, instances