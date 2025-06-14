import logging

from rich.logging import RichHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="🔍 %(levelname)s: %(message)s",
    handlers=[RichHandler(markup=True)],
)
logger = logging.getLogger(__name__)


def get_logger():
    """
    Returns the configured logger instance.
    """
    return logger
