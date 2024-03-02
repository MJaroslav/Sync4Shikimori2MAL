import sync4s2m.config
import logging


__all__ = ["logger", "cfg"]

logger = logging.getLogger("")
logger.setLevel(logging.INFO)
__handler__ = logging.StreamHandler()
__handler__.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(__handler__)

cfg = sync4s2m.config.Config(logger)
cfg.load()
