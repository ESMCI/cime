#!/usr/bin/env python3

import unittest
from unittest import mock

from CIME.SystemTests.mvk import MVK


class TestSystemTestsMVK(unittest.TestCase):
    def test_mvk(self):
        case = mock.MagicMock()
        case.get_value.side_effect = (
            "/tmp/case",  # CASEROOT
            "MVK.f19_g16.S.docker_gnu",  # CASEBASEID
            "mct",  # COMP_INTERFACE
            "MVK.f19_g16.S.docker_gnu",  # CASEBASEID
            "e3sm",  # MODEL
            0,  # RESUBMIT
            False,  # GENERATE_BASELINE
        )

        test = MVK(case)

        assert test.component == "eam"
        assert test.components == ["eam"]
