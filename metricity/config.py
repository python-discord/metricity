"""Configuration reader for Metricity."""
import logging
from os import environ
from pathlib import Path
from typing import Any, Optional

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
    if not Path("config-default.toml").exists():
        raise MetricityConfigurationError("config-default.toml is missing")

    with open("config-default.toml", "r") as default_config_file:
        default_config = toml.load(default_config_file)

    # Load user configuration
    user_config = {}

    if Path("config.toml").exists():
        with open("config.toml", "r") as default_config_file:
            user_config = toml.load(default_config_file)

    # Merge the configuration
    merger = Merger(
        [
            (dict, "merge")
        ],
        ["override"],
        ["override"]
    )

    conf = merger.merge(default_config, user_config)

    # Check whether we are missing the requested section
    if not conf.get(section):
        raise MetricityConfigurationError(
            f"Config is missing section '{section}'"
        )

    return conf[section]


class ConfigSection(type):
    """Metaclass for loading TOML configuration into the relevant class."""

    def __new__(
        cls: type,
        name: str,
        bases: tuple[type],
        dictionary: dict[str, Any]
    ) -> type:
        """Use the section attr in the subclass to fill in the values from the TOML."""
        config = get_section(dictionary["section"])

        log.info(f"Loading configuration section {dictionary['section']}")

        for key, value in config.items():
            if isinstance(value, dict):
                if env_var := value.get("env"):
                    if env_value := environ.get(env_var):
                        config[key] = env_value
                    else:
                        if not value.get("optional"):
                            raise MetricityConfigurationError(
                                f"Required config option '{key}' in"
                                f" '{dictionary['section']}' is missing, either set"
                                f" the environment variable {env_var} or override "
                                "it in your config.toml file"
                            )
                        else:
                            config[key] = None

        dictionary.update(config)

        config_section = super().__new__(cls, name, bases, dictionary)

        return config_section


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
    ignore_categories: list[int]


class DatabaseConfig(metaclass=ConfigSection):
    """Configuration about the database Metricity will use."""

    section = "database"

    uri: Optional[str]

    host: Optional[str]
    port: Optional[int]
    database: Optional[str]
    username: Optional[str]
    password: Optional[str]
