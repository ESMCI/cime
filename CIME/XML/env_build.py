"""
Interface to the env_build.xml file.  This class inherits from EnvBase
"""
from CIME.XML.standard_module_setup import *

from CIME import utils
from CIME.XML.env_base import EnvBase

logger = logging.getLogger(__name__)


class EnvBuild(EnvBase):
    # pylint: disable=unused-argument
    def __init__(
        self, case_root=None, infile="env_build.xml", components=None, read_only=False
    ):
        """
        initialize an object interface to file env_build.xml in the case directory
        """
        schema = os.path.join(utils.get_schema_path(), "env_entry_id.xsd")
        self._caseroot = case_root
        EnvBase.__init__(self, case_root, infile, schema=schema, read_only=read_only)

    def set_value(self, vid, value, subgroup=None, ignore_type=False):
        """
        Set the value of an entry-id field to value
        Returns the value or None if not found
        subgroup is ignored in the general routine and applied in specific methods
        """
        # Do not allow any of these to be the same as CASEROOT
        if vid in ("EXEROOT", "OBJDIR", "LIBROOT"):
            utils.expect(value != self._caseroot, f"Cannot set {vid} to CASEROOT")

        return super(EnvBuild, self).set_value(
            vid, value, subgroup=subgroup, ignore_type=ignore_type
        )
