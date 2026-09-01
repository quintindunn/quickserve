from pathlib import Path
from tomllib import loads
from typing import TYPE_CHECKING, Any, IO, get_args, get_type_hints

import tomli_w
from pydantic import BaseModel, ConfigDict, ValidationError

from QuickServeFS.path_resolver import resolver as _resolver

if TYPE_CHECKING:
    from QuickServeFS.path_resolver import Resolver


class ConfigModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class WebModel(ConfigModel):
    pass

class DriverModel(ConfigModel):
    pass

class DatabaseModel(ConfigModel):
    pass

class Config:
    web: WebModel | None
    driver: DriverModel | None
    database: DatabaseModel | None

    def __init__(self, resolver: "Resolver"):
        self._resolver: "Resolver" = resolver

        self.web = None
        self.driver = None
        self.database = None

        self.read()

    @property
    def config_path(self) -> Path:
        return self._resolver.get_path("config.toml")

    def open_config(self, mode: str) -> "IO[Any]":
        self._resolver.call_if_not_exist(self.config_path, self.create)
        return open(self.config_path, mode=mode)

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

        return models

    def _parse(self, raw: str) -> None:
        data = loads(raw)
        models = self._models()

        for name in data:
            if name not in models:
                raise ValueError(f"Unknown configuration section: {name!r}")

        for name, model in models.items():
            if name not in data:
                continue

            section = data[name]

            if not isinstance(section, dict):
                raise ValueError(
                    f"Configuration section {name!r} must be a TOML table"
                )

            try:
                value = model.model_validate(section)
            except ValidationError as exc:
                raise ValueError(
                    f"Invalid configuration section {name!r}:\n{exc}"
                ) from exc

            setattr(self, name, value)

    def read(self) -> None:
        with self.open_config("r") as f:
            raw = f.read()

        self._parse(raw)

    def create(self, overwrite: bool = False) -> None:
        path = self.config_path

        if path.exists() and not overwrite:
            raise FileExistsError(f"Configuration file already exists: {path}")

        models = self._models()

        data: dict[str, Any] = {}

        for name, model in models.items():
            instance = model()

            data[name] = instance.model_dump(mode="python")

        data = self._toml_safe(data)

        with open(path, "wb") as f:
            tomli_w.dump(data, f)

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
