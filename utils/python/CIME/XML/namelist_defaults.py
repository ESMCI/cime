"""Interface to `namelist_defaults.xml`.

This module contains only one class, `NamelistDefaults`, inheriting from
`GenericXML`.
"""

# Warnings we typically ignore.
# pylint:disable=invalid-name

# Disable warnings due to using `standard_module_setup`
# pylint:disable=wildcard-import,unused-wildcard-import

from CIME.XML.standard_module_setup import *
from CIME.XML.generic_xml import GenericXML

logger = logging.getLogger(__name__)

class NamelistDefaults(GenericXML):

    """Class representing variable default values for a namelist."""

    def __init__(self, infile):
        """Construct a `NamelistDefaults` from an XML file."""
        super(NamelistDefaults, self).__init__(infile)

    def get_value(self, item, attribute=None, resolved=False, subgroup=None):
        """Return the default value for the variable named `item`.

        The return value is a list of strings corresponding to the
        comma-separated list of entries for the value (length 1 for scalars). If
        there is no default value in the file, this returns `None`.
        """
        expect(attribute is None, "This class does not support attributes.")
        expect(not resolved, "This class does not support env resolution.")
        expect(subgroup is None, "This class does not support subgroups.")
        node = self.get_optional_node(item)
        if node is None:
            return None
        if node.text is None:
            return ['']
        # Some trickiness here; we want to split items on commas, but not inside
        # quote-delimited strings. Stripping whitespace is also useful.
        value = []
        pos = 0
        delim = None
        for i, char in enumerate(node.text):
            if delim is None:
                # If not inside a string...
                if char in ('"', "'"):
                    # if we have a quote character, start a string.
                    delim = char
                elif char == ',':
                    # if we have a comma, this is a new value.
                    value.append(node.text[pos:i].strip())
                    pos = i+1
            else:
                # If inside a string, the only thing that can happen is the end
                # of the string.
                if char == delim:
                    delim = None
        value.append(node.text[pos:].strip())
        return value

    # While there are environment variable references in the file at times, they
    # usually involve env files that we don't know about at this low level. So
    # we punt on this issue and make the caller resolve these, if necessary.
    def get_resolved_value(self, raw_value):
        """This function is not implemented."""
        raise TypeError, \
            "NamelistDefaults does not support `get_resolved_value`."
