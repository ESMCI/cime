"""
Interface to the env_archive.xml file.  This class inherits from EnvBase
"""
from standard_module_setup import *

from env_base import EnvBase

logger = logging.getLogger(__name__)

class EnvArchive(EnvBase):
    def __init__(self, case_root=os.getcwd(), infile="env_archive.xml"):
        """
        initialize an object interface to file env_archive.xml in the case directory
        """
        EnvBase.__init__(self, case_root, infile)
