import sys
import os
import glob
import logging
import inspect

from CIME import utils

logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        pass

    @classmethod
    def load(cls, customize_path):
        obj = cls()

        logger.debug("Searching %r for files to load", customize_path)

        customize_files = glob.glob(
            f"{customize_path}/**/*.py",
            recursive=True
        )

        for x in customize_files:
            obj._load_file(x)

        return obj

    def _load_file(self, file_path):
        logger.debug("Loading file %r", file_path)

        raw_config = utils.import_from_file("raw_config", file_path)

        # filter user define variables and functions
        user_defined = [x for x in dir(raw_config) if not x.endswith("__")]

        # set values on this object, will overwrite existing
        for x in user_defined:
            try:
                value = getattr(raw_config, x)
            except AttributeError:
                # should never hit this
                logger.fatal("Attribute %r missing on obejct", x)

                sys.exit(1)
            else:
                self._set_attribute(raw_config, x, value)

    def _set_attribute(self, source, name, value):
        if hasattr(self, name):
            logger.debug("Overwriting %r attribute", name)

        logger.debug("Setting attribute %r with value %r", name, value)

        setattr(self, name, value)
