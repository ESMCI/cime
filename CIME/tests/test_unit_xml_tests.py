#!/usr/bin/env python3

import re
import unittest
import tempfile
from pathlib import Path
from unittest import mock

from CIME.XML.tests import Tests


class TestXMLTests(unittest.TestCase):
    def setUp(self):
        # reset file caching
        Tests._FILEMAP = {}

    # skip hard to mock function call
    @mock.patch(
        "CIME.SystemTests.system_tests_compare_two.SystemTestsCompareTwo._setup_cases_if_not_yet_done"
    )
    def test_support_single_exe(self, _setup_cases_if_not_yet_done):
        with tempfile.TemporaryDirectory() as tdir:
            test_file = Path(tdir) / "sms.py"

            test_file.touch(exist_ok=True)

            caseroot = Path(tdir) / "caseroot1"

            caseroot.mkdir(exist_ok=True)

            case = mock.MagicMock()

            case.get_compset_components.return_value = ()

            def fake_get_value(item, attribute=None):
                simple_lookup = {
                    "TESTCASE": "SMS",
                    "CASEROOT": f"{caseroot}",
                    "CASEBASEID": "SMS.f19_g16.S",
                    "COMP_INTERFACE": "cpl",
                    "DRV_RESTART_POINTER": None,
                }
                if item in simple_lookup:
                    return simple_lookup[item]
                elif item == "SYSTEM_TESTS_DIR":
                    if attribute["component"] == "any":
                        return tdir
                    else:
                        return None

                raise KeyError(
                    f"Unmocked call: case.get_value({item}, attribute={attribute})"
                )

            case.get_value.side_effect = fake_get_value

            tests = Tests()

            tests.support_single_exe(case)

    # skip hard to mock function call
    @mock.patch(
        "CIME.SystemTests.system_tests_compare_two.SystemTestsCompareTwo._setup_cases_if_not_yet_done"
    )
    def test_support_single_exe_error(self, _setup_cases_if_not_yet_done):
        with tempfile.TemporaryDirectory() as tdir:
            test_file = Path(tdir) / "erp.py"

            test_file.touch(exist_ok=True)

            caseroot = Path(tdir) / "caseroot1"

            caseroot.mkdir(exist_ok=True)

            case = mock.MagicMock()

            case.get_compset_components.return_value = ()

            def fake_get_value(item, attribute=None):
                simple_lookup = {
                    "TESTCASE": "ERP",
                    "CASEROOT": f"{caseroot}",
                    "CASEBASEID": "ERP.f19_g16.S",
                    "CASE": "ERP.f19_g16.S",
                    "COMP_INTERFACE": "cpl",
                    "DRV_RESTART_POINTER": None,
                }
                if item in simple_lookup:
                    return simple_lookup[item]
                elif item == "SYSTEM_TESTS_DIR":
                    if attribute["component"] == "any":
                        return tdir
                    else:
                        return None

                raise KeyError(
                    f"Unmocked call: case.get_value({item}, attribute={attribute})"
                )

            case.get_value.side_effect = fake_get_value

            tests = Tests()

            with self.assertRaises(Exception) as e:
                tests.support_single_exe(case)

            assert (
                re.search(
                    r"does not support the '--single-exe' option as it requires separate builds",
                    f"{e.exception}",
                )
                is not None
            ), f"{e.exception}"


if __name__ == "__main__":
    unittest.main()
