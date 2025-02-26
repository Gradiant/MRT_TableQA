from tqa.common.configuration.config import load_config
from tqa.common.configuration.logger import get_logger


def test_config():
    config = load_config()
    print(config)
    assert config != dict()


def test_logger_info():
    logger = get_logger("tests")
    logger.trace("trace message.")
    logger.debug("debug message.")
    logger.info("info message.")
    logger.success("success message.")
    logger.warning("warning message.")
    logger.error("error message.")
    logger.critical("critical message.")
