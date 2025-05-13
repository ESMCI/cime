#!/usr/bin/env python3

import unittest
import tempfile
from unittest import mock

from CIME.XML.env_mach_specific import EnvMachSpecific

# pylint: disable=unused-argument


class TestXMLEnvMachSpecific(unittest.TestCase):
    @mock.patch("CIME.XML.env_mach_specific.EnvMachSpecific.get_optional_child")
    @mock.patch("CIME.XML.env_mach_specific.EnvMachSpecific.text")
    @mock.patch.dict("os.environ", {"TEST_VALUE": "/testexec"})
    def test_init_path(self, text, get_optional_child):
        text.return_value = "$ENV{TEST_VALUE}/init/python"

        mach_specific = EnvMachSpecific()

        value = mach_specific.get_module_system_init_path("python")

        assert value == "/testexec/init/python"

    @mock.patch("CIME.XML.env_mach_specific.EnvMachSpecific.get_optional_child")
    @mock.patch("CIME.XML.env_mach_specific.EnvMachSpecific.text")
    @mock.patch.dict("os.environ", {"TEST_VALUE": "/testexec"})
    def test_cmd_path(self, text, get_optional_child):
        text.return_value = "$ENV{TEST_VALUE}/python"

        mach_specific = EnvMachSpecific()

        value = mach_specific.get_module_system_cmd_path("python")

        assert value == "/testexec/python"
