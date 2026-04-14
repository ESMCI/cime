import unittest

from CIME.simple_compare import _normalize_string_value


class TestSimpleCompare(unittest.TestCase):
    def test_normalize_string_values(self):
        test = "test.grid.compset.mach_compiler"
        testid = "19991231_235959_abcdef"
        for action in ['G', 'C', 'GC']:
            assert(_normalize_string_value(f"{test}.{action}.{testid}", test) == f"{test}.ACTION.TESTID")
