# TESTS GENERATED WITH GENERATIVE AI.

import tempfile
import unittest
from pathlib import Path

import tomli_w

from QuickServeFS.config import (
    Config,
    DatabaseModel,
    DriverModel,
    WebModel,
)
from QuickServeFS.path_resolver import Resolver


class TestModels(unittest.TestCase):
    def test_web_defaults(self):
        model = WebModel()

        self.assertEqual(model.a, 10)
        self.assertEqual(model.b, 20)
        self.assertEqual(model.c, [])

    def test_driver_defaults(self):
        model = DriverModel()

        self.assertTrue(model.a)
        self.assertEqual(model.b, [True, False])
        self.assertEqual(model.c, [[1, 2], [3, 4]])

    def test_database_defaults(self):
        model = DatabaseModel()

        self.assertEqual(model.a, Path("database.db"))
        self.assertEqual(model.b, "username")
        self.assertEqual(model.c, "password")

    def test_models_forbid_extra_fields(self):
        with self.assertRaises(Exception):
            WebModel(unknown="value")


class TestConfigModels(unittest.TestCase):
    def test_get_model(self):
        self.assertIs(Config._get_model(WebModel), WebModel)

    def test_get_model_optional(self):
        self.assertIs(Config._get_model(WebModel | None), WebModel)

    def test_get_model_non_model(self):
        self.assertIsNone(Config._get_model(str))

    def test_models(self):
        self.assertEqual(
            Config._models(),
            {
                "web": WebModel,
                "driver": DriverModel,
                "database": DatabaseModel,
            },
        )


class TestConfigCreate(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.resolver = Resolver(Path(self.temp_dir.name))

    def test_config_is_created_when_missing(self):
        config = Config(self.resolver)

        self.assertTrue(config.config_path.exists())
        self.assertTrue(config.config_path.is_file())

        self.assertEqual(config.web, WebModel())
        self.assertEqual(config.driver, DriverModel())
        self.assertEqual(config.database, DatabaseModel())

    def test_create_writes_default_configuration(self):
        config = Config(self.resolver)
        config.config_path.unlink()

        config.create()

        self.assertTrue(config.config_path.exists())

        raw = config.config_path.read_text()

        self.assertIn("[web]", raw)
        self.assertIn("[driver]", raw)
        self.assertIn("[database]", raw)

    def test_create_serializes_path(self):
        config = Config(self.resolver)
        config.config_path.unlink()

        config.create()

        raw = config.config_path.read_text()

        self.assertIn('a = "database.db"', raw)

    def test_create_raises_if_file_exists(self):
        config = Config(self.resolver)

        with self.assertRaises(FileExistsError):
            config.create()

    def test_create_can_overwrite(self):
        config = Config(self.resolver)

        config.config_path.write_text("old content")

        config.create(overwrite=True)

        self.assertNotEqual(
            config.config_path.read_text(),
            "old content",
        )


class TestConfigParse(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.config = Config(
            Resolver(Path(self.temp_dir.name))
        )

    def test_parse_web(self):
        self.config._parse(
            """
            [web]
            a = 123
            b = 456
            c = ["foo", "bar"]
            """
        )

        self.assertEqual(self.config.web.a, 123)
        self.assertEqual(self.config.web.b, 456)
        self.assertEqual(
            self.config.web.c,
            ["foo", "bar"],
        )

    def test_parse_driver(self):
        self.config._parse(
            """
            [driver]
            a = false
            b = [false, true]
            c = [[10, 20], [30, 40]]
            """
        )

        self.assertFalse(self.config.driver.a)
        self.assertEqual(
            self.config.driver.b,
            [False, True],
        )
        self.assertEqual(
            self.config.driver.c,
            [[10, 20], [30, 40]],
        )

    def test_parse_database(self):
        self.config._parse(
            """
            [database]
            a = "custom.db"
            b = "admin"
            c = "secret"
            """
        )

        self.assertEqual(
            self.config.database.a,
            Path("custom.db"),
        )
        self.assertEqual(
            self.config.database.b,
            "admin",
        )
        self.assertEqual(
            self.config.database.c,
            "secret",
        )

    def test_parse_multiple_sections(self):
        self.config._parse(
            """
            [web]
            a = 1

            [database]
            b = "admin"
            """
        )

        self.assertEqual(self.config.web.a, 1)
        self.assertEqual(self.config.web.b, 20)
        self.assertEqual(self.config.database.b, "admin")

        self.assertEqual(self.config.driver, DriverModel())

    def test_unknown_section(self):
        with self.assertRaisesRegex(
            ValueError,
            r"Unknown configuration section: 'unknown'",
        ):
            self.config._parse(
                """
                [unknown]
                value = 123
                """
            )

    def test_section_must_be_table(self):
        with self.assertRaisesRegex(
            ValueError,
            r"Configuration section 'web' must be a TOML table",
        ):
            self.config._parse("web = 123")

    def test_invalid_web_value(self):
        with self.assertRaisesRegex(
            ValueError,
            r"Invalid configuration section 'web'",
        ):
            self.config._parse(
                """
                [web]
                a = "not an integer"
                """
            )

    def test_invalid_driver_value(self):
        with self.assertRaisesRegex(
            ValueError,
            r"Invalid configuration section 'driver'",
        ):
            self.config._parse(
                """
                [driver]
                b = ["not", "booleans"]
                """
            )

    def test_invalid_database_value(self):
        with self.assertRaisesRegex(
            ValueError,
            r"Invalid configuration section 'database'",
        ):
            self.config._parse(
                """
                [database]
                b = 123
                """
            )

    def test_extra_fields_are_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            r"Invalid configuration section 'web'",
        ):
            self.config._parse(
                """
                [web]
                unknown = "value"
                """
            )

    def test_missing_values_use_defaults(self):
        self.config._parse(
            """
            [web]
            a = 42
            """
        )

        self.assertEqual(self.config.web.a, 42)
        self.assertEqual(self.config.web.b, 20)
        self.assertEqual(self.config.web.c, [])


class TestConfigRead(unittest.TestCase):
    def test_read_loads_configuration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            resolver = Resolver(Path(temp_dir))
            path = resolver.get_path("config.toml")

            path.write_text(
                """
                [web]
                a = 99

                [database]
                b = "alice"
                """
            )

            config = Config(resolver)

            self.assertEqual(config.web.a, 99)
            self.assertEqual(config.database.b, "alice")
            self.assertIsNone(config.driver)

    def test_read_creates_missing_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            resolver = Resolver(Path(temp_dir))

            config = Config(resolver)

            self.assertTrue(config.config_path.exists())


class TestTomlSafe(unittest.TestCase):
    def test_path(self):
        self.assertEqual(
            Config._toml_safe(Path("foo.db")),
            "foo.db",
        )

    def test_dict(self):
        value = {
            "path": Path("database.db"),
            "name": "test",
        }

        self.assertEqual(
            Config._toml_safe(value),
            {
                "path": "database.db",
                "name": "test",
            },
        )

    def test_nested_dict(self):
        value = {
            "database": {
                "path": Path("database.db"),
                "nested": {
                    "other": Path("other.db"),
                },
            }
        }

        self.assertEqual(
            Config._toml_safe(value),
            {
                "database": {
                    "path": "database.db",
                    "nested": {
                        "other": "other.db",
                    },
                }
            },
        )

    def test_list(self):
        value = [Path("a"), Path("b")]

        self.assertEqual(
            Config._toml_safe(value),
            ["a", "b"],
        )

    def test_nested_list(self):
        value = [[Path("a")], [Path("b")]]

        self.assertEqual(
            Config._toml_safe(value),
            [["a"], ["b"]],
        )

    def test_tuple_becomes_list(self):
        value = (Path("a"), Path("b"))

        self.assertEqual(
            Config._toml_safe(value),
            ["a", "b"],
        )

    def test_output_is_toml_serializable(self):
        value = {
            "path": Path("database.db"),
            "items": [
                Path("a"),
                {"nested": Path("b")},
            ],
        }

        safe = Config._toml_safe(value)

        # Should not raise.
        output = tomli_w.dumps(safe)

        self.assertIn(
            'path = "database.db"',
            output,
        )


if __name__ == "__main__":
    unittest.main()
