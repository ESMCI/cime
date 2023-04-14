#!/usr/bin/env python3

import unittest
import io

from CIME.XML import tests

SINGLE_EXE_DEFAULT_INVALID = """<?xml version="1.0"?>
<config_test>
  <test NAME="AAA">
    <INFO_DBUG>1</INFO_DBUG>
    <STOP_OPTION>ndays</STOP_OPTION>
    <STOP_N>4</STOP_N>
    <HIST_OPTION>ndays</HIST_OPTION>
    <HIST_N>1</HIST_N>
    <DOUT_S>FALSE</DOUT_S>
  </test>
</config_test>
"""

SINGLE_EXE_VALID = """<?xml version="1.0"?>
<config_test>
  <test NAME="AAA">
    <SINGLE_EXE>true</SINGLE_EXE>
    <INFO_DBUG>1</INFO_DBUG>
    <STOP_OPTION>ndays</STOP_OPTION>
    <STOP_N>4</STOP_N>
    <HIST_OPTION>ndays</HIST_OPTION>
    <HIST_N>1</HIST_N>
    <DOUT_S>FALSE</DOUT_S>
  </test>
</config_test>
"""

SINGLE_EXE_INVALID = """<?xml version="1.0"?>
<config_test>
  <test NAME="AAA">
    <SINGLE_EXE>false</SINGLE_EXE>
    <INFO_DBUG>1</INFO_DBUG>
    <STOP_OPTION>ndays</STOP_OPTION>
    <STOP_N>4</STOP_N>
    <HIST_OPTION>ndays</HIST_OPTION>
    <HIST_N>1</HIST_N>
    <DOUT_S>FALSE</DOUT_S>
  </test>
</config_test>
"""


class TestXMLTests(unittest.TestCase):
    def setUp(self):
        # reset file caching
        tests.Tests._FILEMAP = {}

    def test_support_single_exe_default_invalid(self):
        buffer = io.StringIO(SINGLE_EXE_DEFAULT_INVALID)

        xml_tests = tests.Tests()

        xml_tests.read_fd(buffer)

        valid, invalid = xml_tests.support_single_exe(["AAA.f19_g16.A"])

        assert valid == []
        assert invalid == ["AAA.f19_g16.A"]

    def test_support_single_exe_valid(self):
        buffer = io.StringIO(SINGLE_EXE_VALID)

        xml_tests = tests.Tests()

        xml_tests.read_fd(buffer)

        valid, invalid = xml_tests.support_single_exe(["AAA.f19_g16.A"])

        assert valid == ["AAA.f19_g16.A"]
        assert invalid == []

    def test_support_single_exe_invalid(self):
        buffer = io.StringIO(SINGLE_EXE_INVALID)

        xml_tests = tests.Tests()

        xml_tests.read_fd(buffer)

        valid, invalid = xml_tests.support_single_exe(["AAA.f19_g16.A"])

        assert valid == []
        assert invalid == ["AAA.f19_g16.A"]

if __name__ == "__main__":
    unittest.main()
