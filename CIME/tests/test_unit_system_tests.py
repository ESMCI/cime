#!/usr/bin/env python3

import os
from re import A
import unittest
from unittest import mock
from pathlib import Path

from CIME.SystemTests.system_tests_common import SystemTestsCommon
from CIME.SystemTests.system_tests_compare_two import SystemTestsCompareTwo
from CIME.SystemTests.system_tests_compare_n import SystemTestsCompareN


class TestCaseSubmit(unittest.TestCase):
    def test_kwargs(self):
        case = mock.MagicMock()

        case.get_value.side_effect = (
            "/caseroot",
            "SMS.f19_g16.S",
            "cpl",
            "/caseroot",
            "SMS.f19_g16.S",
        )

        _ = SystemTestsCommon(case, something="random")

        case = mock.MagicMock()

        case.get_value.side_effect = (
            "/caseroot",
            "SMS.f19_g16.S",
            "cpl",
            "/caseroot",
            "SMS.f19_g16.S",
        )

        orig1 = SystemTestsCompareTwo._get_caseroot
        orig2 = SystemTestsCompareTwo._get_caseroot2

        SystemTestsCompareTwo._get_caseroot = mock.MagicMock()
        SystemTestsCompareTwo._get_caseroot2 = mock.MagicMock()

        _ = SystemTestsCompareTwo(case, something="random")

        SystemTestsCompareTwo._get_caseroot = orig1
        SystemTestsCompareTwo._get_caseroot2 = orig2

        case = mock.MagicMock()

        case.get_value.side_effect = (
            "/caseroot",
            "SMS.f19_g16.S",
            "cpl",
            "/caseroot",
            "SMS.f19_g16.S",
        )

        orig = SystemTestsCompareN._get_caseroots

        SystemTestsCompareN._get_caseroots = mock.MagicMock()

        _ = SystemTestsCompareN(case, something="random")

        SystemTestsCompareN._get_caseroots = orig

    def test_dry_run(self):
        case = mock.MagicMock()

        case.get_value.side_effect = (
            "/caseroot",
            "SMS.f19_g16.S",
            "cpl",
            "/caseroot",
            "SMS.f19_g16.S",
        )

        orig = SystemTestsCompareTwo._setup_cases_if_not_yet_done

        SystemTestsCompareTwo._setup_cases_if_not_yet_done = mock.MagicMock()

        system_test = SystemTestsCompareTwo(case, dry_run=True)

        system_test._setup_cases_if_not_yet_done.assert_not_called()

        case = mock.MagicMock()

        case.get_value.side_effect = (
            "/caseroot",
            "SMS.f19_g16.S",
            "cpl",
            "/caseroot",
            "SMS.f19_g16.S",
        )

        system_test = SystemTestsCompareTwo(case)

        system_test._setup_cases_if_not_yet_done.assert_called()

        SystemTestsCompareTwo._setup_cases_if_not_yet_done = orig

        orig = SystemTestsCompareN._setup_cases_if_not_yet_done

        SystemTestsCompareN._setup_cases_if_not_yet_done = mock.MagicMock()

        case = mock.MagicMock()

        case.get_value.side_effect = (
            "/caseroot",
            "SMS.f19_g16.S",
            "cpl",
            "/caseroot",
            "SMS.f19_g16.S",
        )

        system_test = SystemTestsCompareN(case, dry_run=True)

        system_test._setup_cases_if_not_yet_done.assert_not_called()

        case = mock.MagicMock()

        case.get_value.side_effect = (
            "/caseroot",
            "SMS.f19_g16.S",
            "cpl",
            "/caseroot",
            "SMS.f19_g16.S",
        )

        system_test = SystemTestsCompareN(case)

        system_test._setup_cases_if_not_yet_done.assert_called()

        SystemTestsCompareN._setup_cases_if_not_yet_done = orig
