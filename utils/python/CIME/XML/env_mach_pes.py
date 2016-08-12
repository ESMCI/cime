"""
Interface to the env_mach_pes.xml file.  This class inherits from EntryID
"""
from CIME.XML.standard_module_setup import *

from CIME.XML.entry_id import EntryID

logger = logging.getLogger(__name__)

class EnvMachPes(EntryID):

    @staticmethod
    def constructEnvMachPes(case_root, infile = "env_mach_pes.xml"):
        return EnvMachPes.construct(case_root, infile)

    def get_value(self, vid, attribute=None, resolved=True, subgroup=None):
        value = EntryID.get_value(self, vid, attribute, resolved, subgroup)
        if "NTASKS" in vid and value < 0:
            value = -1*value*self.get_value("PES_PER_NODE")
        if "NTHRDS" in vid and value < 0:
            value = -1*value*self.get_value("PES_PER_NODE")
        if "ROOTPE" in vid and value < 0:
            value = -1*value*self.get_value("PES_PER_NODE")
        return value
    #
    # We need a set value until we full transition from perl
    #

    def _set_value(self, node, value, vid=None, subgroup=None, ignore_type=False):
        if vid is None:
            vid = node.get("id")

        if "NTASKS" in vid and value < 0:
            value = -1*value*self.get_value("PES_PER_NODE")
        if "NTHRDS" in vid and value < 0:
            value = -1*value*self.get_value("PES_PER_NODE")
        if "ROOTPE" in vid and value < 0:
            value = -1*value*self.get_value("PES_PER_NODE")
        val = EntryID._set_value(self, node, value, vid, subgroup, ignore_type)
        return val
