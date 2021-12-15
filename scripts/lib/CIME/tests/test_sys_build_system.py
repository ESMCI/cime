#!/usr/bin/env python3

from CIME.tests import base


class TestBuildSystem(base.BaseTestCase):
    def test_clean_rebuild(self):
        casedir = self._create_test(
            ["--no-run", "SMS.f19_g16_rx1.A"], test_id=self._baseline_name
        )

        # Clean a component and a sharedlib
        self.run_cmd_assert_result("./case.build --clean atm", from_dir=casedir)
        self.run_cmd_assert_result("./case.build --clean gptl", from_dir=casedir)

        # Repeating should not be an error
        self.run_cmd_assert_result("./case.build --clean atm", from_dir=casedir)
        self.run_cmd_assert_result("./case.build --clean gptl", from_dir=casedir)

        self.run_cmd_assert_result("./case.build", from_dir=casedir)
