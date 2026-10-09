"""
Tests the api blueprint for the flask app.

Author: Quintin Dunn
Date: 10/09/2026
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from flask import Flask

from QuickServe.Web.api import api


class TestAPI(TestCase):
    """
    Tests for the API blueprint.
    """

    def setUp(self):
        """
        Set up the test client and dependencies.
        """

        self.app = Flask(__name__, template_folder="templates")
        self.app.register_blueprint(api)
        self.app.extensions["quickserve.search"] = MagicMock()
        self.app.extensions["quickserve.catalog"] = MagicMock()
        self.app.extensions["quickserve.instance_manager"] = MagicMock()
        self.client = self.app.test_client()

    def test_search_without_query(self):
        """
        Test searching without a query.
        """

        response = self.client.get("/api/v1/search")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"")

    def test_search_no_results(self):
        """
        Test searching when no results are found.
        """

        self.app.extensions["quickserve.search"].search.return_value = ([], [])

        response = self.client.get("/api/v1/search?query=unknown")

        self.assertEqual(response.status_code, 204)
        self.app.extensions["quickserve.search"].search.assert_called_once_with(
            query="unknown", max_results=5
        )

    def test_search_results(self):
        """
        Test searching with module and instance results.
        """

        module = MagicMock()
        module_result = (MagicMock(identifier="module-id"),)
        instance_result = (MagicMock(identifier="instance-id"),)
        instance = MagicMock()

        search = self.app.extensions["quickserve.search"]
        catalog = self.app.extensions["quickserve.catalog"]
        instance_manager = self.app.extensions["quickserve.instance_manager"]

        search.search.return_value = ([module_result], [instance_result])
        catalog.get.return_value.module = module
        instance_manager.from_uuid.return_value = instance

        with patch("QuickServe.Web.api.render_template") as render_template:
            render_template.return_value = "results"

            response = self.client.get("/api/v1/search?query=test")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"results")
        search.search.assert_called_once_with(query="test", max_results=5)
        catalog.get.assert_called_once_with("module-id")
        instance_manager.from_uuid.assert_called_once_with("instance-id")
        render_template.assert_called_once_with(
            "core/search.html",
            context={"modules": [module], "instances": [instance]},
        )

    def test_search_modules_only(self):
        """
        Test searching when only modules are found.
        """

        module_result = (MagicMock(identifier="module-id"),)
        module = MagicMock()

        search = self.app.extensions["quickserve.search"]
        catalog = self.app.extensions["quickserve.catalog"]

        search.search.return_value = ([module_result], [])
        catalog.get.return_value.module = module

        with patch("QuickServe.Web.api.render_template") as render_template:
            render_template.return_value = "results"

            response = self.client.get("/api/v1/search?query=test")

        self.assertEqual(response.status_code, 200)
        render_template.assert_called_once_with(
            "core/search.html",
            context={"modules": [module], "instances": []},
        )
