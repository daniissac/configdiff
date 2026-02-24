"""Logging configuration for ConfigDiff."""

from __future__ import annotations

import logging
import sys


def setup_logging(*, verbose: bool = False) -> None:
    """Configure the root ``configdiff`` logger."""
    level = logging.DEBUG if verbose else logging.WARNING
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(levelname)s: %(name)s: %(message)s")
    )
    logger = logging.getLogger("configdiff")
    logger.setLevel(level)
    logger.addHandler(handler)
