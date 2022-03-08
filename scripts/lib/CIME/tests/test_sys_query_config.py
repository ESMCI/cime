#!/usr/bin/env python3

from CIME import utils
from CIME.tests import base


class TestQueryConfig(base.BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_query_compsets(self):
        utils.run_cmd_no_fail("{}/query_config --compsets".format(self.SCRIPT_DIR))

    def test_query_components(self):
        utils.run_cmd_no_fail("{}/query_config --components".format(self.SCRIPT_DIR))

    def test_query_grids(self):
        utils.run_cmd_no_fail("{}/query_config --grids".format(self.SCRIPT_DIR))

    def test_query_machines(self):
        utils.run_cmd_no_fail("{}/query_config --machines".format(self.SCRIPT_DIR))
