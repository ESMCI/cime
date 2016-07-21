"""Interface to `namelist_definition.xml`.

This module contains only one class, `NamelistDefinition`, inheriting from
`GenericXML`.
"""

# Disable warnings due to using `standard_module_setup`
# pylint:disable=wildcard-import,unused-wildcard-import

from CIME.XML.standard_module_setup import *
from CIME.XML.generic_xml import GenericXML


class NamelistDefinition(GenericXML):

    """Class representing variable definitions for a namelist."""

    def __init__(self, infile):
        """Construct a `NamelistDefinition` from an XML file."""
        super(NamelistDefinition, self).__init__(infile)

    def get_value(self, item, attribute=None, resolved=False, subgroup=None):
        """Get data about the namelist variable named `item`.

        The returned value will be a dict with the following keys:
         - type
         - category
         - group
         - valid_values
         - input_pathname
         - description

        All such values will be strings, except that `valid_values` will be a
        list of valid values for the namelist variable to take, or `None` if no
        such constraint is provided.
        """
        expect(attribute is None, "This class does not support attributes.")
        expect(not resolved, "This class does not support env resolution.")
        expect(subgroup is None, "This class does not support subgroups.")
        elem = self.get_node("entry", attributes={'id': item})
        var_info = {}

        def get_required_field(name):
            """Copy a required attribute from `entry` element to `var_info`."""
            var_info[name] = elem.get(name)
            expect(var_info[name] is not None,
                   "field %s missing from namelist definition for %s" %
                   (name, item))

        get_required_field('type')
        get_required_field('category')
        get_required_field('group')
        # The "valid_values" attribute is not required, and an empty string has
        # the same effect as not specifying it.
        valid_values = elem.get('valid_values')
        if valid_values == '':
            valid_values = None
        if valid_values is not None:
            valid_values = valid_values.split(',')
        var_info['valid_values'] = valid_values
        # The "input_pathname" attribute is not required.
        var_info['input_pathname'] = elem.get('input_pathname')
        # The description is the data on the node itself.
        var_info['description'] = elem.text
        return var_info

    # Currently we don't use this object to construct new files, and it's no
    # good for that purpose anyway, so stop this function from being called.
    def set_value(self, vid, value, subgroup=None, ignore_type=True):
        """This function is not implemented."""
        raise TypeError, \
            "NamelistDefinition does not support `set_value`."

    # There seems to be no good use for this capability in this file, so it is
    # unimplemented.
    def get_resolved_value(self, raw_value):
        """This function is not implemented."""
        raise TypeError, \
            "NamelistDefinition does not support `get_resolved_value`."
