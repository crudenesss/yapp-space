"""Filter classes for logging objects"""

import logging


class FilterDebug(logging.Filter):
    """Only records with level DEBUG can pass"""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelname == "DEBUG"


class FilterInfo(logging.Filter):
    """Only records with level above DEBUG can pass"""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelname == "INFO"
