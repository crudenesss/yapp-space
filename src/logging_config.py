"""Special configuration for logging with gunicorn"""

from os import getenv
from utils.filters import FilterDebug, FilterInfo

LOG_LEVEL = getenv("LOGGING_LEVEL")

# Define the logging configuration
logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "general": {
            "format": "[%(levelname)s] - %(asctime)s - %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
        "detailed": {
            "format": 
            "[%(levelname)s] - %(asctime)s - %(message)s - in %(pathname)s:%(funcName)s:%(lineno)d",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        }
    },
    "filters": {
        "filter_debug": {
            "()": FilterDebug,
        },
        "filter_info": {
            "()": FilterInfo,
        },
    },
    "handlers": {
        "stdout_debug": {
            "class": "logging.StreamHandler",
            "formatter": "detailed",
            "filters": ["filter_debug"],
            "level": "DEBUG",
        },
        "stdout_default": {
            "class": "logging.StreamHandler",
            "formatter": "general",
            "filters": ["filter_info"],
            "level": "INFO",
        },
        "stdout_error": {
            "class": "logging.StreamHandler",
            "formatter": "detailed",
            "level": "ERROR",
        }
    },
    "root": {"handlers": ["stdout_default", "stdout_debug", "stdout_error"], "level": "INFO"},
    "loggers": {
        "gunicorn.access": {
            "handlers": ["stdout_default", "stdout_debug", "stdout_error"],
            "level": LOG_LEVEL,
            "propagate": False,
        }
    }
}
