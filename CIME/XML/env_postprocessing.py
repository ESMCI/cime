"""
Interface to the env_postprocessing.xml file.  This class inherits from EnvBase
"""

import logging
import os

from CIME import utils
from CIME.XML.env_base import EnvBase

logger = logging.getLogger(__name__)


class EnvPostprocessing(EnvBase):
    def __init__(
        self, case_root=None, infile="env_postprocessing.xml", read_only=False
    ):
        """
        initialize an object interface to file env_postprocessing.xml in the case directory
        """
        schema = os.path.join(utils.get_schema_path(), "env_entry_id.xsd")

        EnvBase.__init__(self, case_root, infile, schema=schema, read_only=read_only)
