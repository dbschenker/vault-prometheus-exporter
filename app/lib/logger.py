import logging
import json_log_formatter


def setup():
    """
    Setup custom JSON log handler and remove old handlers.

    :return: None
    """
    logger = logging.getLogger()
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])
    logger_root = logging.getLogger()
    logger_root.setLevel(logging.INFO)
    logHandler = logging.StreamHandler()
    logHandler.setFormatter(json_log_formatter.VerboseJSONFormatter())
    logger_root.addHandler(logHandler)
