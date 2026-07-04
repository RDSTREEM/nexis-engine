import logging
from rich.logging import RichHandler


def setup_logger():
    logging.basicConfig(level="INFO", format="%(message)s", handlers=[RichHandler()])

    return logging.getLogger("Nexis Engine")
