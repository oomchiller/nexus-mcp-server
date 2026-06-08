import logging
import re

from typing import Optional, Pattern

class RedactingFormatter(logging.Formatter):
    """Formatter that redacts sensitive information."""

    def __init__(self, fmt: str | None = None, datefmt: str | None = None, secrets: list[str] | None = None):
        super().__init__(fmt, datefmt)
        self.secrets = [re.escape(s) for s in (secrets or []) if s]
        self.regex: Optional[Pattern[str]] = None
        if self.secrets:
            self.regex = re.compile(f"({'|'.join(self.secrets)})")

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        if self.regex:
            return self.regex.sub("********", msg)
        return msg

def setup_logging(level: str = "INFO", secrets: list[str] | None = None) -> None:
    """Set up structured logging with secret redaction."""
    logger = logging.getLogger("nexus_mcp_server")
    logger.setLevel(level)

    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()

    handler = logging.StreamHandler()
    formatter = RedactingFormatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        secrets=secrets
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(f"nexus_mcp_server.{name}")
