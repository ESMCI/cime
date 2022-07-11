"""
Interface to the env_run.xml file.  This class inherits from EnvBase
"""
from CIME.XML.standard_module_setup import *

from CIME.XML.env_base import EnvBase

from CIME import utils
from CIME.utils import convert_to_type

logger = logging.getLogger(__name__)


class EnvRun(EnvBase):
    def __init__(
        self, case_root=None, infile="env_run.xml", components=None, read_only=False
    ):
        """
        initialize an object interface to file env_run.xml in the case directory
        """
        self._components = components
#        self._pio_async_interface = {}
#
#        if components:
#            for comp in components:
#                if comp not in self._pio_async_interface:
#                    self._pio_async_interface[comp] = False

        schema = os.path.join(utils.get_schema_path(), "env_entry_id.xsd")

        EnvBase.__init__(self, case_root, infile, schema=schema, read_only=read_only)

    def get_value(self, vid, attribute=None, resolved=True, subgroup=None):
        """
        Get a value for entry with id attribute vid.
        or from the values field if the attribute argument is provided
        and matches.   Special case for pio variables when PIO_ASYNC_INTERFACE is True.
        """
#        if any(self._pio_async_interface.values()):
#            vid, comp, iscompvar = self.check_if_comp_var(vid, attribute)

        return EnvBase.get_value(self, vid, attribute, resolved, subgroup)

    def set_value(self, vid, value, subgroup=None, ignore_type=False):
        """
        Set the value of an entry-id field to value
        Returns the value or None if not found
        subgroup is ignored in the general routine and applied in specific methods
        """
        vid, comp, iscompvar = self.check_if_comp_var(vid, None)

#        print(f"before {comp} {self._pio_async_interface}")
#        if vid == "PIO_ASYNC_INTERFACE":
#            if type(value) == type(True):
#                self._pio_async_interface[comp] = value
#            else:
#                self._pio_async_interface[comp] = convert_to_type(value, "logical", vid)

#        print(f"after {comp} {self._pio_async_interface}")
        return EnvBase.set_value(self, vid, value, subgroup, ignore_type)
