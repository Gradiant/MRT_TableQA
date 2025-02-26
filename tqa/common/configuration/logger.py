import os
import sys

from loguru import logger

from tqa.common.configuration.config import CONFIG_PATH, load_config

# remove sys.stderr initial to avoid duplicate ouputs
logger.remove()
# get config and set up log folder
CONFIG = load_config()
CONFIG_LOGGER = load_config(filename="logger.yaml")

LOG_PATH = (
    os.path.join(CONFIG_PATH, CONFIG["log_path"])
    if CONFIG["log_path"].startswith(".")
    else CONFIG["log_path"]
)
os.makedirs(LOG_PATH, exist_ok=True)

LOGGERS = {}


def get_logger(logger_name: str):

    if logger_name in LOGGERS:
        return LOGGERS.get(logger_name)

    if logger_name in CONFIG_LOGGER:
        logger.add(
            os.path.join(LOG_PATH, "{}.log".format(logger_name)),
            filter=lambda record: record["extra"]["task"] == logger_name,
            **CONFIG_LOGGER[logger_name],
        )
        logger.add(
            sink=sys.stderr,
            filter=lambda record: record["extra"]["task"] == logger_name,
            level=CONFIG_LOGGER[logger_name].get("level"),
        )

        LOGGERS[logger_name] = logger.bind(task=logger_name)
        return logger.bind(task=logger_name)
    else:
        CONFIG_LOGGER[logger_name] = {"level": "TRACE", "rotation": "2MB"}
        logger.add(
            os.path.join(LOG_PATH, "{}.log".format(logger_name)),
            filter=lambda record: record["extra"]["task"] == logger_name,
            **CONFIG_LOGGER[logger_name],
        )
        out_logger = logger.bind(task=logger_name)
        out_logger.error(
            "This logger {} is not defined in logger.yaml.".format(logger_name)
        )
        LOGGERS[logger_name] = out_logger
        return logger.bind(task=logger_name)
