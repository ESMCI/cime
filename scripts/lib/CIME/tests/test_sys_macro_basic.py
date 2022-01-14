#!/usr/bin/env python3

from xml.etree.ElementTree import ParseError

from CIME import utils
from CIME.tests import base
from CIME.tests import utils as test_utils
from CIME.XML.compilers import Compilers

import os

class TestMacrosBasic(base.BaseTestCase):
    """Basic infrastructure tests.

    This class contains tests that do not actually depend on the output of the
    macro file conversion. This includes basic smoke testing and tests of
    error-handling in the routine.
    """

    def setUp(self):
        super().setUp()

        if "CIME_NO_CMAKE_MACRO" not in os.environ:
            self.skipTest("Skipping test of old macro system")

    def test_script_is_callable(self):
        """The test script can be called on valid output without dying."""
        # This is really more a smoke test of this script than anything else.
        maker = Compilers(test_utils.MockMachines("mymachine", "SomeOS"), version=2.0)
        test_xml = test_utils._wrap_config_compilers_xml(
            "<compiler><SUPPORTS_CXX>FALSE</SUPPORTS_CXX></compiler>"
        )
        test_utils.get_macros(maker, test_xml, "Makefile")

    def test_script_rejects_bad_xml(self):
        """The macro writer rejects input that's not valid XML."""
        maker = Compilers(test_utils.MockMachines("mymachine", "SomeOS"), version=2.0)
        with self.assertRaises(ParseError):
            test_utils.get_macros(maker, "This is not valid XML.", "Makefile")

    def test_script_rejects_bad_build_system(self):
        """The macro writer rejects a bad build system string."""
        maker = Compilers(test_utils.MockMachines("mymachine", "SomeOS"), version=2.0)
        bad_string = "argle-bargle."
        with self.assertRaisesRegex(
            utils.CIMEError,
            "Unrecognized build system provided to write_macros: " + bad_string,
        ):
            test_utils.get_macros(maker, "This string is irrelevant.", bad_string)
