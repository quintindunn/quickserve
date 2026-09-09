from pathlib import Path
from tomllib import loads

from typing import Any, IO, get_args, get_type_hints

import logging

import tomli_w
from pydantic import BaseModel, ConfigDict, ValidationError

from QuickServeFS.path_resolver import resolver as _resolver
from QuickServeFS.path_resolver import Resolver

logger = logging.getLogger("QuickServeFS.config")


class ConfigModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class WebModel(ConfigModel):
    secret_key: str = "secret-key-change-in-production"


class DriverModel(ConfigModel):
    pass


class DatabaseModel(ConfigModel):
    file_path: str = "/opt/quickserve/database.db"


class Config:
    web: WebModel | None
    driver: DriverModel | None
    database: DatabaseModel | None
    resolver: Resolver

    def __init__(self, resolver: "Resolver"):
        logger.debug("Initializing configuration")

        self.resolver: "Resolver" = resolver

        self.web = None
        self.driver = None
        self.database = None

        self.read()

        logger.info("Configuration loaded successfully")

    @property
    def config_path(self) -> Path:
        return self.resolver.get_path("config.toml")

    def open_config(self, mode: str) -> "IO[Any]":
        path = self.config_path

        logger.debug("Opening configuration file %s with mode %r", path, mode)

        try:
            self.resolver.call_if_not_exist(path, self.create)
            return open(path, mode=mode)
        except OSError:
            logger.exception("Failed to open configuration file %s", path)
            raise

    @staticmethod
    def _get_model(annotation: Any) -> type[BaseModel] | None:
        for arg in get_args(annotation) or (annotation,):
            if isinstance(arg, type) and issubclass(arg, BaseModel):
                return arg

        return None

    @classmethod
    def _models(cls) -> dict[str, type[BaseModel]]:
        annotations = get_type_hints(cls)

        models = {}

        for name, annotation in annotations.items():
            model = cls._get_model(annotation)

            if model is not None:
                models[name] = model

        logger.debug(
            "Discovered configuration models: %s",
            ", ".join(models),
        )

        return models

    def _parse(self, raw: str) -> None:
        logger.debug("Parsing configuration")

        try:
            data = loads(raw)
        except Exception:
            logger.exception("Failed to parse configuration TOML")
            raise

        if not isinstance(data, dict):
            raise ValueError("Configuration root must be a TOML table")

        models = self._models()

        logger.debug(
            "Configuration contains sections: %s",
            ", ".join(data) if data else "<none>",
        )

        for name in data:
            if name not in models:
                logger.error("Unknown configuration section: %r", name)
                raise ValueError(f"Unknown configuration section: {name!r}")

        for name, model in models.items():
            if name not in data:
                logger.debug(
                    "Configuration section %r not present; leaving default value",
                    name,
                )
                continue

            section = data[name]

            if not isinstance(section, dict):
                logger.error(
                    "Configuration section %r is not a TOML table",
                    name,
                )
                raise ValueError(f"Configuration section {name!r} must be a TOML table")

            logger.debug(
                "Validating configuration section %r with %s",
                name,
                model.__name__,
            )

            try:
                value = model.model_validate(section)
            except ValidationError as exc:
                logger.error(
                    "Validation failed for configuration section %r",
                    name,
                )
                raise ValueError(
                    f"Invalid configuration section {name!r}:\n{exc}"
                ) from exc

            setattr(self, name, value)

            logger.debug(
                "Loaded configuration section %r",
                name,
            )

    def read(self) -> None:
        path = self.config_path

        logger.info("Reading configuration from %s", path)

        try:
            with self.open_config("r") as f:
                raw = f.read()
        except OSError:
            logger.exception(
                "Failed to read configuration file %s",
                path,
            )
            raise

        logger.debug(
            "Read %d bytes from configuration file",
            len(raw),
        )

        self._parse(raw)

    def create(self, overwrite: bool = False) -> None:
        path = self.config_path

        logger.info(
            "Creating configuration file %s%s",
            path,
            " (overwriting existing file)" if overwrite else "",
        )

        if path.exists() and not overwrite:
            logger.error(
                "Refusing to overwrite existing configuration file %s",
                path,
            )
            raise FileExistsError(f"Configuration file already exists: {path}")

        models = self._models()

        data: dict[str, Any] = {}

        for name, model in models.items():
            logger.debug(
                "Generating default configuration section %r using %s",
                name,
                model.__name__,
            )

            instance = model()
            data[name] = instance.model_dump(mode="python")

        data = self._toml_safe(data)

        try:
            with open(path, "wb") as f:
                tomli_w.dump(data, f)
        except OSError:
            logger.exception(
                "Failed to write configuration file %s",
                path,
            )
            raise

        logger.info("Configuration file created at %s", path)

    @staticmethod
    def _toml_safe(value: Any) -> Any:
        """
        Convert Python values into values that TOML can serialize.
        """
        if isinstance(value, Path):
            return str(value)

        if isinstance(value, dict):
            return {key: Config._toml_safe(val) for key, val in value.items()}

        if isinstance(value, list):
            return [Config._toml_safe(item) for item in value]

        if isinstance(value, tuple):
            return [Config._toml_safe(item) for item in value]

        return value


config = Config(resolver=_resolver)
