#!/usr/bin/env python3

from CIME import utils
from CIME.tests import base
from CIME.XML.files import Files


class TestManageAndQuery(base.BaseTestCase):
    """Tests various scripts to manage and query xml files"""

    def setUp(self):
        super().setUp()

        if self._config.test_mode == "e3sm":
            self.skipTest("Skipping XML test management tests. E3SM does not use this.")

    def _run_and_assert_query_testlist(self, extra_args=""):
        """Ensure that query_testlist runs successfully with the given extra arguments"""
        files = Files()
        testlist_drv = files.get_value("TESTS_SPEC_FILE", {"component": "drv"})

        self.run_cmd_assert_result(
            "{}/query_testlists --xml-testlist {} {}".format(
                self.SCRIPT_DIR, testlist_drv, extra_args
            )
        )

    def test_query_testlists_runs(self):
        """Make sure that query_testlists runs successfully

        This simply makes sure that query_testlists doesn't generate any errors
        when it runs. This helps ensure that changes in other utilities don't
        break query_testlists.
        """
        self._run_and_assert_query_testlist(extra_args="--show-options")

    def test_query_testlists_define_testtypes_runs(self):
        """Make sure that query_testlists runs successfully with the --define-testtypes argument"""
        self._run_and_assert_query_testlist(extra_args="--define-testtypes")

    def test_query_testlists_count_runs(self):
        """Make sure that query_testlists runs successfully with the --count argument"""
        self._run_and_assert_query_testlist(extra_args="--count")

    def test_query_testlists_list_runs(self):
        """Make sure that query_testlists runs successfully with the --list argument"""
        self._run_and_assert_query_testlist(extra_args="--list categories")
