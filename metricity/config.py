"""Configuration reader for Metricity."""
import logging
from os import environ
from pathlib import Path
from typing import Any

import toml
from deepmerge import Merger
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)


class MetricityConfigurationError(Exception):
    """Exception signifying something has gone awry whilst parsing Metricity config."""


def get_section(section: str) -> dict[str, Any]:
    """
    Load the section config from config-default.toml and config.toml.

    Use deepmerge.Merger to merge the configuration from config.toml
    and override that of config-default.toml.
    """
    # Load default configuration
    default_config_file = Path("config-default.toml")
    if not default_config_file.exists():
        raise MetricityConfigurationError("config-default.toml is missing")

    with default_config_file.open() as default_config_file:
        default_config = toml.load(default_config_file)

    # Load user configuration
    user_config = {}
    user_config_location = Path(environ.get("CONFIG_LOCATION", "./config.toml"))

    if user_config_location.exists():
        with Path.open(user_config_location) as user_config_file:
            user_config = toml.load(user_config_file)

    # Merge the configuration
    merger = Merger(
        [
            (dict, "merge"),
        ],
        ["override"],
        ["override"],
    )

    conf = merger.merge(default_config, user_config)

    # Check whether we are missing the requested section
    if not conf.get(section):
        raise MetricityConfigurationError(f"Config is missing section '{section}'")

    return conf[section]


class ConfigSection(type):
    """Metaclass for loading TOML configuration into the relevant class."""

    def __new__(
        cls: type,
        name: str,
        bases: tuple[type],
        dictionary: dict[str, Any],
    ) -> type:
        """Use the section attr in the subclass to fill in the values from the TOML."""
        config = get_section(dictionary["section"])

        log.info("Loading configuration section %s", dictionary["section"])

        for key, value in config.items():
            if isinstance(value, dict) and (env_var := value.get("env")):
                if env_value := environ.get(env_var):
                    config[key] = env_value
                elif not value.get("optional"):
                    raise MetricityConfigurationError(
                        f"Required config option '{key}' in"
                        f" '{dictionary['section']}' is missing, either set"
                        f" the environment variable {env_var} or override "
                        "it in your config.toml file",
                    )
                else:
                    config[key] = None

        dictionary.update(config)

        return super().__new__(cls, name, bases, dictionary)


class PythonConfig(metaclass=ConfigSection):
    """Settings relating to the Python environment the application runs in."""

    section = "python"

    log_level: str
    discord_log_level: str


class BotConfig(metaclass=ConfigSection):
    """Configuration for the Metricity bot."""

    section = "bot"

    token: str

    guild_id: int
    staff_role_id: int

    staff_categories: list[int]
    staff_channels: list[int]
    ignore_categories: list[int]


class DatabaseConfig(metaclass=ConfigSection):
    """Configuration about the database Metricity will use."""

    section = "database"

    uri: str | None

    host: str | None
    port: int | None
    database: str | None
    username: str | None
    password: str | None
