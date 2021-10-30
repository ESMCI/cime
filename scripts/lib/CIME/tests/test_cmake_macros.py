#!/usr/bin/env python3

from CIME.tests import base
from CIME.tests import utils as test_utils


class TestCMakeMacros(base.BaseTestCase):
    """CMake macros tests.

    This class contains tests of the CMake output of Build.

    This class simply inherits all of the methods of TestMakeOutput, but changes
    the definition of xml_to_tester to create a CMakeTester instead.
    """

    def xml_to_tester(self, xml_string):
        """Helper that directly converts an XML string to a MakefileTester."""
        test_xml = test_utils._wrap_config_compilers_xml(xml_string)
        if (self.NO_CMAKE):
            self.skipTest("Skipping cmake test")
        else:
            return test_utils.CMakeTester(self, test_utils.get_macros(self._maker, test_xml, "CMake"))
