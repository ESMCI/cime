"""
Interface to the env_run.xml file.  This class inherits from EnvBase
"""
from itertools import zip_longest
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
        self._pio_async_interface = {}

        if components:
            for comp in components:
                self._pio_async_interface[comp] = False

        schema = os.path.join(utils.get_schema_path(), "env_entry_id.xsd")

        EnvBase.__init__(self, case_root, infile, schema=schema, read_only=read_only)

    def get_value(self, vid, attribute=None, resolved=True, subgroup=None):
        """
        Get a value for entry with id attribute vid.
        or from the values field if the attribute argument is provided
        and matches.   Special case for pio variables when PIO_ASYNC_INTERFACE is True.
        """
        if any(self._pio_async_interface.values()):
            vid, comp, iscompvar = self.check_if_comp_var(vid, attribute)
            if vid.startswith("PIO") and iscompvar:
                if comp and comp != "CPL":
                    logger.warning("Only CPL settings are used for PIO in async mode")
                subgroup = "CPL"

        return EnvBase.get_value(self, vid, attribute, resolved, subgroup)

    def set_value(self, vid, value, subgroup=None, ignore_type=False):
        """
        Set the value of an entry-id field to value
        Returns the value or None if not found
        subgroup is ignored in the general routine and applied in specific methods
        """
        comp = None
        if any(self._pio_async_interface.values()):
            vid, comp, iscompvar = self.check_if_comp_var(vid, None)
            if vid.startswith("PIO") and iscompvar:
                if comp and comp != "CPL":
                    logger.warning("Only CPL settings are used for PIO in async mode")
                subgroup = "CPL"

        if vid == "PIO_ASYNC_INTERFACE":
            if comp:
                if type(value) == type(True):
                    self._pio_async_interface[comp] = value
                else:
                    self._pio_async_interface[comp] = convert_to_type(
                        value, "logical", vid
                    )
        # PIO_NETCDF_FORMAT=64bit_data is not compatible with PIO_TYPENAME=netcdf4p
        # make sure that this combination of options is not set
        if "PIO_TYPENAME" in vid or "PIO_NETCDF_FORMAT" in vid:
            nvid, comp, iscompvar = self.check_if_comp_var(vid, None)
            pio_netcdf_formats = []
            pio_typenames = []

            if nvid == "PIO_TYPENAME":
                if comp:
                    pio_netcdf_formats = [
                        self.get_value("PIO_NETCDF_FORMAT_{}".format(comp.upper()))
                    ]
                else:
                    pio_netcdf_formats = self.get_values("PIO_NETCDF_FORMAT")
                pio_typenames = [value]
            elif nvid == "PIO_NETCDF_FORMAT":
                if comp:
                    pio_typenames = [
                        self.get_value("PIO_TYPENAME_{}".format(comp.upper()))
                    ]
                else:
                    pio_typenames = self.get_values("PIO_TYPENAME")
                pio_netcdf_formats = [value]

            last_format = pio_netcdf_formats[-1]
            last_typename = pio_typenames[-1]
            for pio_typename, pio_netcdf_format in zip_longest(
                pio_typenames, pio_netcdf_formats
            ):
                if pio_typename is None:
                    pio_typename = last_typename
                if pio_netcdf_format is None:
                    pio_netcdf_format = last_format

                incompatible_pio_typenames = ("netcdf4p", "netcdf4c")
                expect(
                    not (
                        pio_typename in incompatible_pio_typenames
                        and "64bit_data" in pio_netcdf_format
                    ),
                    "pio_typename {} is not compatible with pio_netcdf_format {}".format(
                        pio_typename, pio_netcdf_format
                    ),
                )

        return EnvBase.set_value(self, vid, value, subgroup, ignore_type)
