"""
Interface to the env_archive.xml file.  This class inherits from EnvBase
"""
from CIME.XML.standard_module_setup import *
from CIME import utils
from CIME.XML.archive_base import ArchiveBase
from CIME.XML.env_base import EnvBase

logger = logging.getLogger(__name__)
# pylint: disable=super-init-not-called
class EnvArchive(ArchiveBase, EnvBase):
    def __init__(self, case_root=None, infile="env_archive.xml", read_only=False):
        """
        initialize an object interface to file env_archive.xml in the case directory
        """
        schema = os.path.join(utils.get_schema_path(), "env_archive.xsd")
        EnvBase.__init__(self, case_root, infile, schema=schema, read_only=read_only)

    def get_type_info(self, vid):
        return "char"
