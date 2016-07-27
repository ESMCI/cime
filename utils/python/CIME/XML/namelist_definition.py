"""Interface to `namelist_definition.xml`.

This module contains only one class, `NamelistDefinition`, inheriting from
`GenericXML`.
"""

# Warnings we typically ignore.
# pylint:disable=invalid-name

# Disable warnings due to using `standard_module_setup`
# pylint:disable=wildcard-import,unused-wildcard-import

import re

from CIME.namelist import fortran_namelist_base_value, \
    is_valid_fortran_namelist_literal, character_literal_to_string, \
    expand_literal_list, Namelist

from CIME.XML.standard_module_setup import *
from CIME.XML.generic_xml import GenericXML

logger = logging.getLogger(__name__)

_array_size_re = re.compile(r'^(?P<type>[^(]+)\((?P<size>[^)]+)\)$')

class NamelistDefinition(GenericXML):

    """Class representing variable definitions for a namelist."""

    def __init__(self, infile):
        """Construct a `NamelistDefinition` from an XML file."""
        super(NamelistDefinition, self).__init__(infile)

    def add(self, infile):
        """Add the contents of an XML file to the namelist definition."""
        new_root = ET.parse(infile).getroot()
        for elem in new_root:
            self.root.append(elem)

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
        elem = self.get_node("entry", attributes={'id': item.lower()})
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

    @staticmethod
    def _split_type_string(name, type_string):
        """Split a 'type' attribute string into its component parts.

        The `name` argument is the variable name associated with this type
        string. It is used for error reporting purposes.

        The return value is a tuple consisting of the type itself, a length
        (which is an integer for character variables, otherwise `None`), and the
        size of the array (which is 1 for scalar variables).

        This method also checks to ensure that the input `type_string` is valid.
        """
        # 'char' is frequently used as an abbreviation of 'character'.
        type_string = type_string.replace('char', 'character')
        # Separate into a size and the rest of the type.
        size_match = _array_size_re.search(type_string)
        if size_match:
            type_string = size_match.group('type')
            size_string = size_match.group('size')
            try:
                size = int(size_string)
            except ValueError:
                expect(False,
                       "In namelist definition, variable %s had the "
                       "non-integer string %r specified as an array size." %
                       (name, size_string))
        else:
            size = 1
        # Separate into a type and an optional length.
        type_, star, length = type_string.partition('*')
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
        else:
            max_len = None
        return type_, max_len, size

    @staticmethod
    def _canonicalize_value(type_, value):
        """Create 'canonical' version of a value for comparison purposes."""
        canonical_value = [fortran_namelist_base_value(scalar)
                           for scalar in value]
        canonical_value = [scalar for scalar in canonical_value if scalar != '']
        if type_ == 'character':
            canonical_value = [character_literal_to_string(scalar)
                               for scalar in canonical_value]
        elif type_ == 'integer':
            canonical_value = [int(scalar) for scalar in canonical_value]
        return canonical_value

    def is_valid_value(self, name, value):
        """Determine whether a value is valid for the named variable.

        The `value` argument must be a list of strings formatted as they would
        appear in the namelist (even for scalar variables, in which case the
        length of the list is always 1).
        """
        name = name.lower()
        var_info = self.get_value(name)
        # Separate into a type, optional length, and optional size.
        type_, max_len, size = self._split_type_string(name, var_info["type"])
        # Check value against type.
        for scalar in value:
            if not is_valid_fortran_namelist_literal(type_, scalar):
                return False
        # Now that we know that the strings as input are valid Fortran, do some
        # canonicalization for further checks.
        canonical_value = self._canonicalize_value(type_, value)
        # Check maximum length (if applicable).
        if max_len is not None:
            for scalar in canonical_value:
                if len(scalar) > max_len:
                    return False
        # Check valid value constraints (if applicable).
        if var_info["valid_values"] is not None:
            expect(type_ in ('integer', 'character'),
                   "Found valid_values attribute for variable %s with "
                   "type %s, but valid_values only allowed for character "
                   "and integer variables." % (name, type_))
            if type_ == 'integer':
                compare_list = [int(vv)
                                for vv in var_info["valid_values"]]
            else:
                compare_list = var_info["valid_values"]
            for scalar in canonical_value:
                if scalar not in compare_list:
                    return False
        # Check size of input array.
        if len(expand_literal_list(value)) > size:
            return False
        return True

    def _expect_variable_in_definition(self, name):
        """Used to get a better error message for an unexpected variable."""
        node = self.get_optional_node("entry", attributes={'id': name})
        expect(node is not None,
               "Variable %r is not in the namelist definition." % str(name))

    def validate(self, namelist):
        """Validate a namelist object against this definition."""
        for group_name in namelist.get_group_names():
            for variable_name in namelist.get_variable_names(group_name):
                self._expect_variable_in_definition(variable_name)
                var_info = self.get_value(variable_name)
                expect(var_info['group'] == group_name,
                       "Variable %r is in a group named %r, but should be in "
                       "%r." % (str(variable_name), str(group_name),
                                str(var_info['group'])))
                value = namelist.get_variable_value(group_name, variable_name)
                expect(self.is_valid_value(variable_name, value),
                       "Variable %r has invalid value %r." %
                       (str(variable_name), [str(scalar) for scalar in value]))

    def dict_to_namelist(self, dict_):
        """Converts a dictionary of name-value pairs to a `Namelist`.

        The input is assumed to be similar to the output of `parse` when
        `groupless=True` is set. This function uses the namelist definition file
        to look up the namelist group associated with each variable, and uses
        this information to create a true `Namelist` object.
        """
        groups = {}
        for variable_name in dict_:
            variable_lc = variable_name.lower()
            self._expect_variable_in_definition(variable_lc)
            var_info = self.get_value(variable_lc)
            group_name = var_info['group']
            if group_name not in groups:
                groups[group_name] = {}
            groups[group_name][variable_lc] = dict_[variable_name]
        return Namelist(groups)
