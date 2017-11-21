"""
Interface to the config_tests.xml file.  This class inherits from GenericEntry
"""
from CIME.XML.standard_module_setup import *

from CIME.XML.generic_xml import GenericXML
from CIME.XML.files import Files

logger = logging.getLogger(__name__)

class Tests(GenericXML):

    def __init__(self,  infile=None, files=None):
        """
        initialize an object interface to file config_tests.xml
        """
        if infile is None:
            if files is None:
                files = Files()
            infile = files.get_value("CONFIG_TESTS_FILE")
        GenericXML.__init__(self,  infile)
        # append any component specific config_tests.xml files
        for comp in files.get_components("CONFIG_TESTS_FILE"):
            if comp is None:
                continue
            infile = files.get_value("CONFIG_TESTS_FILE", attribute={"component":comp})
            if os.path.isfile(infile):
                self.read(infile)

    def get_test_node(self, testname):
        logger.debug("Get settings for {}".format(testname))
        node = self.get_node("test",{"NAME":testname})
        logger.debug("Found {}".format(node.text))
        return node

    def print_values(self, skip_infrastructure_tests=True):
        """
        Print each test type and its description.

        If skip_infrastructure_tests is True, then this does not write
        information for tests with the attribute
        INFRASTRUCTURE_TEST="TRUE".
        """
        all_tests = self.get_nodes(nodename="test")
        for one_test in all_tests:
            if skip_infrastructure_tests:
                infrastructure_test = one_test.get("INFRASTRUCTURE_TEST")
                if (infrastructure_test is not None and
                    infrastructure_test.upper() == "TRUE"):
                    continue
            name = one_test.get("NAME")
            desc = one_test.find("DESC").text
            print("{}: {}".format(name, desc))
