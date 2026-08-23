import logging, sys
import structlog
from app.core.config import settings

def configure_logging():
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=getattr(logging, settings.log_level.upper(), logging.INFO))
    structlog.configure(processors=[structlog.contextvars.merge_contextvars, structlog.processors.add_log_level, structlog.processors.TimeStamper(fmt="iso", utc=True), structlog.processors.JSONRenderer()], wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, settings.log_level.upper(), logging.INFO)))
