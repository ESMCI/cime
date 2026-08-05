# Unit tests for mizuRoute baseline namelist comparison transition logic.
import unittest
import tempfile
import os
import shutil

from CIME.case.case_cmpgen_namelists import _do_full_nl_comp

class TestMizuRouteNamelistCompare(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.caseroot = os.path.join(self.tempdir, "caseroot")
        self.casedocs = os.path.join(self.caseroot, "CaseDocs")
        self.baseline_root = os.path.join(self.tempdir, "baselines")
        
        self.compare_name = "test_cmp"
        self.test_name = "test_case"
        
        self.baseline_dir = os.path.join(self.baseline_root, self.compare_name, self.test_name)
        self.baseline_casedocs = os.path.join(self.baseline_dir, "CaseDocs")
        
        os.makedirs(self.casedocs)
        os.makedirs(self.baseline_casedocs)

    def tearDown(self):
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_baseline_has_only_control(self):
        """Verify comparison passes when baseline contains only legacy mizuRoute.control file while CaseDocs contains both."""
        # Setup generated CaseDocs with both
        with open(os.path.join(self.casedocs, "mizuRoute.control"), "w") as f:
            f.write("route_opt 5\n")
        with open(os.path.join(self.casedocs, "mizuroute.toml"), "w") as f:
            f.write("[route_opt]\nvalue = 5\n")
            
        # Setup baseline with ONLY .control
        with open(os.path.join(self.baseline_casedocs, "mizuRoute.control"), "w") as f:
            f.write("route_opt 5\n")
            
        match, comments = _do_full_nl_comp(self.caseroot, self.test_name, self.compare_name, self.baseline_root)
        
        # Baseline lacks mizuroute.toml, but transition logic in _do_full_nl_comp tolerates missing twin config file
        self.assertTrue(match)

    def test_baseline_has_both(self):
        """Verify comparison prefers mizuroute.toml and ignores mizuRoute.control when both exist in baseline."""
        # Setup generated CaseDocs with both
        with open(os.path.join(self.casedocs, "mizuRoute.control"), "w") as f:
            f.write("route_opt 5\n")
        with open(os.path.join(self.casedocs, "mizuroute.toml"), "w") as f:
            f.write("[route_opt]\nvalue = 5\n")
            
        # Setup baseline with BOTH, but with legacy .control having mismatching content
        with open(os.path.join(self.baseline_casedocs, "mizuRoute.control"), "w") as f:
            f.write("route_opt 999\n")
        with open(os.path.join(self.baseline_casedocs, "mizuroute.toml"), "w") as f:
            f.write("[route_opt]\nvalue = 5\n")
            
        match, comments = _do_full_nl_comp(self.caseroot, self.test_name, self.compare_name, self.baseline_root)
        self.assertTrue(match)

    def test_baseline_has_only_toml(self):
        """Verify comparison passes when baseline contains only migrated mizuroute.toml while CaseDocs contains both."""
        # Setup generated CaseDocs with both
        with open(os.path.join(self.casedocs, "mizuRoute.control"), "w") as f:
            f.write("route_opt 5\n")
        with open(os.path.join(self.casedocs, "mizuroute.toml"), "w") as f:
            f.write("[route_opt]\nvalue = 5\n")
            
        # Setup baseline with ONLY .toml
        with open(os.path.join(self.baseline_casedocs, "mizuroute.toml"), "w") as f:
            f.write("[route_opt]\nvalue = 5\n")
            
        match, comments = _do_full_nl_comp(self.caseroot, self.test_name, self.compare_name, self.baseline_root)
        
        # Baseline lacks mizuRoute.control, but transition logic in _do_full_nl_comp tolerates missing twin config file
        self.assertTrue(match)

    def test_baseline_has_neither(self):
        """Verify comparison fails when baseline contains neither mizuRoute.control nor mizuroute.toml."""
        # Setup generated CaseDocs with both
        with open(os.path.join(self.casedocs, "mizuRoute.control"), "w") as f:
            f.write("route_opt 5\n")
        with open(os.path.join(self.casedocs, "mizuroute.toml"), "w") as f:
            f.write("[route_opt]\nvalue = 5\n")
            
        # Baseline casedocs is empty (neither file exists)
        match, comments = _do_full_nl_comp(self.caseroot, self.test_name, self.compare_name, self.baseline_root)
        
        self.assertFalse(match)
        self.assertIn("Missing baseline namelist", comments)

    def test_casedocs_has_only_toml_baseline_has_control(self):
        """Verify comparison fails when CaseDocs contains only mizuroute.toml but baseline contains only legacy mizuRoute.control."""
        # Setup generated CaseDocs with ONLY .toml
        with open(os.path.join(self.casedocs, "mizuroute.toml"), "w") as f:
            f.write("[route_opt]\nvalue = 5\n")

        # Setup baseline with ONLY .control
        with open(os.path.join(self.baseline_casedocs, "mizuRoute.control"), "w") as f:
            f.write("route_opt 5\n")

        match, comments = _do_full_nl_comp(self.caseroot, self.test_name, self.compare_name, self.baseline_root)
        self.assertFalse(match)
        self.assertIn("Missing baseline namelist", comments)

    def test_casedocs_has_only_control_baseline_has_toml(self):
        """Verify comparison fails when CaseDocs contains only mizuRoute.control but baseline contains only migrated mizuroute.toml."""
        # Setup generated CaseDocs with ONLY .control
        with open(os.path.join(self.casedocs, "mizuRoute.control"), "w") as f:
            f.write("route_opt 5\n")

        # Setup baseline with ONLY .toml
        with open(os.path.join(self.baseline_casedocs, "mizuroute.toml"), "w") as f:
            f.write("[route_opt]\nvalue = 5\n")

        match, comments = _do_full_nl_comp(self.caseroot, self.test_name, self.compare_name, self.baseline_root)
        self.assertFalse(match)
        self.assertIn("Missing baseline namelist", comments)

if __name__ == '__main__':
    unittest.main()


