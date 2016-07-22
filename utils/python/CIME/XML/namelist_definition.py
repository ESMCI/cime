"""Interface to `namelist_definition.xml`.

This module contains only one class, `NamelistDefinition`, inheriting from
`GenericXML`.
"""

# Disable warnings due to using `standard_module_setup`
# pylint:disable=wildcard-import,unused-wildcard-import

from CIME.namelist import fortran_namelist_base_value, \
    is_valid_fortran_namelist_literal

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

    def is_valid_value(self, name, value):
        """Determine whether a value is valid for the named variable.

        The `value` argument must be a list of strings formatted as they would
        appear in the namelist (even for scalar variables, in which case the
        length of the list is always 1).
        """
        var_info = self.get_value(name)
        # 'char' is frequently used as an abbreviation of 'character'.
        type_string = var_info["type"].replace('char', 'character')
        # Separate into a type and an optional length.
        type_, star, length = type_string.partition('*')
        for scalar in value:
            if not is_valid_fortran_namelist_literal(type_, scalar):
                return False
        # Now that we know that the strings as input are valid Fortran, do some
        # canonicalization for further checks.
        canonical_value = [fortran_namelist_base_value(scalar)
                           for scalar in value]
        if type_ == 'character':
            for i, scalar in enumerate(canonical_value):
                # Figure out whether a quote or apostrophe is the delimiter.
                delimiter = None
                for char in scalar:
                    if char in ("'", '"'):
                        delimiter = char
                # If neither, this is a null value.
                if delimiter is None:
                    continue
                # Find left and right edges of the string, extract middle.
                left_pos = scalar.find(delimiter)
                right_pos = scalar.rfind(delimiter)
                new_scalar = scalar[left_pos+1:right_pos]
                # Replace escaped quote and apostrophe characters.
                canonical_value[i] = new_scalar.replace(delimiter * 2,
                                                        delimiter)
        if star == '*':
            # Length allowed only for character variables.
            expect(type_ == 'character',
                   "In namelist definition, length specified for non-character "
                   "variable %s." % name)
            # Check that the length is actually an integer, to make the error
            # message a bit cleaner if the xml input is bad.
            try:
                max_len = int(length)
            except ValueError:
                expect(False,
                       "In namelist definition, character variable %s had the "
                       "non-integer string %r specified as a length." %
                       (name, length))
            for scalar in canonical_value:
                if len(scalar) > max_len:
                    return False
        if var_info["valid_values"] is not None:
            for scalar in canonical_value:
                if scalar != '' and scalar not in var_info["valid_values"]:
                    return False
        return True
