import logging

from uvicorn.config import LOGGING_CONFIG

from .settings import settings

LOG_LEVEL: int = logging.DEBUG if settings.DEBUG else logging.INFO
LOG_LEVEL_STR: int = 'DEBUG' if settings.DEBUG else 'INFO'

LOGGING_CONFIG["formatters"]["default"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
LOGGING_CONFIG["formatters"]["default"]["fmt"] = "(%(asctime)s) %(levelprefix)s %(message)s"
LOGGING_CONFIG["formatters"]["access"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
LOGGING_CONFIG["formatters"]["access"]["fmt"] = '(%(asctime)s) %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
LOGGING_CONFIG["loggers"]["uvicorn"]["level"] = LOG_LEVEL_STR

logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger('uvicorn')
