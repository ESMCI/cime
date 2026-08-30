# Unit tests for CIME.compare_namelists TOML comparison functions.
import unittest
import tempfile
import os

from CIME.compare_namelists import compare_namelist_files, is_namelist_file

class TestCompareNamelists(unittest.TestCase):
    def test_toml_whitespace_handling(self):
        """Verify that TOML comparison ignores arbitrary whitespace and comments when matching key-value pairs."""
        gold_toml = """
[route_opt]
value = 5
# a comment
"""
        compare_toml = """
   [ route_opt ]    
        value      =       5
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix="_toml") as f1, \
             tempfile.NamedTemporaryFile(mode="w", delete=False, suffix="_toml") as f2:
            f1.write(gold_toml)
            f2.write(compare_toml)
            f1_name = f1.name
            f2_name = f2.name

        try:
            self.assertTrue(is_namelist_file(f1_name))
            match, comments = compare_namelist_files(f1_name, f2_name)
            self.assertTrue(match)
            self.assertEqual(comments, "")
        finally:
            os.remove(f1_name)
            os.remove(f2_name)

    def test_toml_compare_diff(self):
        """Verify that TOML comparison correctly detects and reports mismatched key-value values."""
        gold_toml = """
[route_opt]
value = 5

[physics]
method = "IRF"
"""
        compare_toml = """
[route_opt]
value = 5

[physics]
method = "MC"
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix="_toml") as f1, \
             tempfile.NamedTemporaryFile(mode="w", delete=False, suffix="_toml") as f2:
            f1.write(gold_toml)
            f2.write(compare_toml)
            f1_name = f1.name
            f2_name = f2.name

        try:
            match, comments = compare_namelist_files(f1_name, f2_name)
            self.assertFalse(match)
            self.assertIn("method had mismatched values", comments)
        finally:
            os.remove(f1_name)
            os.remove(f2_name)

    def test_underscore_toml_extension(self):
        """Verify TOML files ending in _toml (such as mizuroute_toml) are correctly parsed as TOML namelists."""
        content = "[route_opt]\nvalue = 5\n"
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix="_toml") as f1, \
             tempfile.NamedTemporaryFile(mode="w", delete=False, suffix="_toml") as f2:
            f1.write(content)
            f2.write(content)
            f1_name = f1.name
            f2_name = f2.name

        try:
            self.assertTrue(is_namelist_file(f1_name))
            match, comments = compare_namelist_files(f1_name, f2_name)
            self.assertTrue(match)
        finally:
            os.remove(f1_name)
            os.remove(f2_name)


