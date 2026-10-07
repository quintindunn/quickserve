import logging
from typing import Tuple

from bs4 import BeautifulSoup

from QuickServe.Application.instances import InstanceManager
from QuickServe.Common.tf_idf import TfIDF
from QuickServe.Driver.instance.base_instance import BaseInstance
from QuickServe.FileSystem.plugins import ModuleCatalog
from QuickServe.contracts import Module

logger = logging.getLogger(__name__)


class Search:
    module_tfidf: TfIDF
    instance_tfidf: TfIDF
    module_registrar: set[str]

    catalog: "ModuleCatalog"
    instance_manager: "InstanceManager"

    def __init__(
        self,
        catalog: "ModuleCatalog",
        instance_manager: "InstanceManager",
    ):
        self.module_tfidf = TfIDF()
        self.instance_tfidf = TfIDF()
        self.module_registrar = set()
        self.instance_registrar = set()

        self.instance_manager = instance_manager
        self.catalog = catalog

        logger.debug("Initialized search")

    @staticmethod
    def _build_module_tfidf_add(module: "Module") -> Tuple[str, str, str]:
        title = f"{module.NAME} {module.VERSION}"
        soup = BeautifulSoup(module.about(), features="html.parser")
        body = f"{module.DESCRIPTION}\n\n{soup.text}"
        return title, body, ""

    @staticmethod
    def _build_instance_tfidf_add(
        instance: "BaseInstance",
    ) -> Tuple[str, str, str]:
        title = f"{instance.instance_name} {instance.module_name} {instance.uuid}"
        return title, "", ""

    def register_module(self, module: "Module"):
        if module.NAME in self.module_registrar:
            logger.debug(f"Module {module.NAME!r} is already registered")
            return

        logger.debug(f"Registering module {module.NAME!r}")

        self.module_registrar.add(module.NAME)
        title, body, minor = self._build_module_tfidf_add(module)
        self.module_tfidf.add_result(
            identifier=module.NAME,
            title=title,
            text=body,
            minor=minor,
        )

    def register_instance(self, instance: "BaseInstance"):
        identifier = str(instance.uuid)

        if identifier in self.instance_registrar:
            logger.debug(f"Instance {identifier!r} is already registered")
            return

        logger.debug(f"Registering instance {identifier!r}")

        self.instance_registrar.add(identifier)
        title, body, minor = self._build_instance_tfidf_add(instance=instance)
        self.instance_tfidf.add_result(
            identifier=identifier,
            title=title,
            text=body,
            minor=minor,
        )

    def update_modules(self):
        logger.info("Updating module search index")

        for _, module in self.catalog.items():
            self.register_module(module.module)

        logger.info(
            f"Module search index contains " f"{len(self.module_registrar)} modules"
        )

    def update_instances(self):
        logger.info("Updating instance search index")

        for instance in self.instance_manager.load_all():
            self.register_instance(instance)

        logger.info(
            f"Instance search index contains "
            f"{len(self.instance_registrar)} instances"
        )

    def update_all(self):
        logger.info("Updating search indexes")

        self.update_modules()
        self.update_instances()

        logger.info("Finished updating search indexes")

    def search(self, query: str, max_results: int = 5):
        logger.info(f"Searching for {query!r} with max results {max_results}")

        modules = self.module_tfidf.query(
            query=query,
            max_results=max_results,
        )
        instances = self.instance_tfidf.query(
            query=query,
            max_results=max_results,
        )

        logger.info(
            f"Search for {query!r} returned "
            f"{len(modules)} modules and {len(instances)} instances"
        )

        return modules, instances
