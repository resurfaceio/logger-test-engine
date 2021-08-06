from pathlib import Path
from loguru import logger
import sys


BASEDIR = Path(__file__).resolve().parent.parent

logger.remove()
logger.add(
    BASEDIR / "logs" / "logs.log",
    enqueue=True,
    backtrace=True,
)
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time}</green> <level>{message}</level>",
    level="INFO",
)

IS_DEV = False
LOCAL_URL = "http://localhost"
DB_HOST = "resurfacedb.eastus.azurecontainer.io"
DB_PORT = 4000
