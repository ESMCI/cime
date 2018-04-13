"""
Interface to the config_headers.xml file.  This class inherits from EntryID.py
"""
from CIME.XML.standard_module_setup import *

from CIME.XML.generic_xml import GenericXML
from CIME.XML.files import Files

logger = logging.getLogger(__name__)

class Headers(GenericXML):
    def __init__(self,infile=None):
        """
        initialize an object

        >>> files = Files()
        >>> files.get_value('CASEFILE_HEADERS',resolved=False)
        '$CIMEROOT/config/config_headers.xml'
        """
        if infile is None:
            files = Files()
            infile = files.get_value('CASEFILE_HEADERS', resolved=True)
        super(Headers, self).__init__(infile)

    def get_header_node(self, fname):
        fnode = self.get_child("file", attributes={"name" : fname})
        headernode = self.get_child("header", root=fnode)
        return headernode
