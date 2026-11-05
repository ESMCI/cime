#!/usr/bin/env python3

"""Unit tests for env_build.py compclass support."""

import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path

from CIME.core.exceptions import CIMEError
from CIME.XML.env_build import EnvBuild


def _open_temp_file(stack, content):
    """Helper to create a temporary XML file with given content."""
    file_obj = stack.enter_context(
        tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False)
    )
    file_obj.write(content)
    file_obj.close()
    return file_obj


ENV_BUILD_BASE = """<?xml version="1.0" encoding="UTF-8"?>
<file id="env_build.xml" version="2.0">
  <header>
    These variables control the build environment.
  </header>
  <group id="build_settings">
    <entry id="EXEROOT" value="/path/to/exe">
      <type>char</type>
      <desc>Root directory for executable</desc>
    </entry>
    <entry id="OBJDIR" value="/path/to/obj">
      <type>char</type>
      <desc>Root directory for object files</desc>
    </entry>
    <entry id="COMP_BOOST_OPTION" value="">
      <type>char</type>
      <desc>Component boost option</desc>
      <values>
        <value compclass="atm">boost_atm</value>
        <value compclass="lnd">boost_lnd</value>
        <value compclass="ocn">boost_ocn</value>
      </values>
    </entry>
    <entry id="COMP_BUILD_FLAG" value="">
      <type>logical</type>
      <desc>Component build flag</desc>
      <values>
        <value compclass="atm">TRUE</value>
        <value compclass="lnd">FALSE</value>
      </values>
    </entry>
  </group>
</file>
"""

ENV_BUILD_NO_COMPCLASS = """<?xml version="1.0" encoding="UTF-8"?>
<file id="env_build.xml" version="2.0">
  <header>
    These variables control the build environment.
  </header>
  <group id="build_settings">
    <entry id="EXEROOT" value="/path/to/exe">
      <type>char</type>
      <desc>Root directory for executable</desc>
    </entry>
  </group>
</file>
"""


def test_env_build_suffixed_component_values(tmp_path):
    # Context
    infile = tmp_path / "env_build.xml"
    infile.write_text(ENV_BUILD_BASE)
    env_build = EnvBuild(infile=str(infile), components=["atm", "lnd", "ocn"])

    # Act
    original_value = env_build.get_value("COMP_BOOST_OPTION_atm")
    resolved_value = env_build.get_resolved_value("${COMP_BOOST_OPTION_atm}")
    env_build.set_value("COMP_BOOST_OPTION_atm", "new_atm_value")

    # Assert
    assert original_value == "boost_atm"
    assert resolved_value == "boost_atm"
    assert env_build.get_value("COMP_BOOST_OPTION_atm") == "new_atm_value"
    assert env_build.get_value("COMP_BOOST_OPTION_lnd") == "boost_lnd"
    assert env_build.get_value("COMP_BOOST_OPTION_ocn") == "boost_ocn"


class TestEnvBuild(unittest.TestCase):
    """Test cases for EnvBuild class."""

    def test_env_build_init_with_components(self):
        """Test that EnvBuild stores components parameter."""
        with ExitStack() as stack:
            temp_file = _open_temp_file(stack, ENV_BUILD_BASE)
            components = ["atm", "lnd", "ocn"]
            env_build = EnvBuild(infile=temp_file.name, components=components)

            # Verify _components is set
            self.assertEqual(env_build._components, components)

    def test_env_build_init_without_components(self):
        """Test that EnvBuild handles None components."""
        with ExitStack() as stack:
            temp_file = _open_temp_file(stack, ENV_BUILD_BASE)
            env_build = EnvBuild(infile=temp_file.name, components=None)

            # Verify _components is None
            self.assertIsNone(env_build._components)

    def test_env_build_get_compclass_value(self):
        """Test getting component-scoped values with compclass."""
        with ExitStack() as stack:
            temp_file = _open_temp_file(stack, ENV_BUILD_BASE)
            components = ["atm", "lnd", "ocn"]
            env_build = EnvBuild(infile=temp_file.name, components=components)

            # Get values for each component
            atm_value = env_build.get_value(
                "COMP_BOOST_OPTION", attribute={"compclass": "atm"}
            )
            self.assertEqual(atm_value, "boost_atm")

            lnd_value = env_build.get_value(
                "COMP_BOOST_OPTION", attribute={"compclass": "lnd"}
            )
            self.assertEqual(lnd_value, "boost_lnd")

            ocn_value = env_build.get_value(
                "COMP_BOOST_OPTION", attribute={"compclass": "ocn"}
            )
            self.assertEqual(ocn_value, "boost_ocn")

    def test_env_build_set_compclass_value(self):
        """Test setting component-scoped values with compclass."""
        with ExitStack() as stack:
            temp_file = _open_temp_file(stack, ENV_BUILD_BASE)
            components = ["atm", "lnd", "ocn"]
            env_build = EnvBuild(infile=temp_file.name, components=components)

            # When setting a component variable without specifying a component,
            # it sets the value for all components in self._components
            env_build.set_value("COMP_BOOST_OPTION", "new_boost_value")

            # Verify all components have the same value
            atm_value = env_build.get_value(
                "COMP_BOOST_OPTION", attribute={"compclass": "atm"}
            )
            self.assertEqual(atm_value, "new_boost_value")

            lnd_value = env_build.get_value(
                "COMP_BOOST_OPTION", attribute={"compclass": "lnd"}
            )
            self.assertEqual(lnd_value, "new_boost_value")

            ocn_value = env_build.get_value(
                "COMP_BOOST_OPTION", attribute={"compclass": "ocn"}
            )
            self.assertEqual(ocn_value, "new_boost_value")

    def test_env_build_get_compclass_logical_value(self):
        """Test getting logical component-scoped values."""
        with ExitStack() as stack:
            temp_file = _open_temp_file(stack, ENV_BUILD_BASE)
            components = ["atm", "lnd"]
            env_build = EnvBuild(infile=temp_file.name, components=components)

            # Get logical values for each component
            atm_value = env_build.get_value(
                "COMP_BUILD_FLAG", attribute={"compclass": "atm"}
            )
            self.assertTrue(atm_value)

            lnd_value = env_build.get_value(
                "COMP_BUILD_FLAG", attribute={"compclass": "lnd"}
            )
            self.assertFalse(lnd_value)

    def test_env_build_non_component_entry(self):
        """Test that non-component entries work normally."""
        with ExitStack() as stack:
            temp_file = _open_temp_file(stack, ENV_BUILD_NO_COMPCLASS)
            components = ["atm", "lnd"]
            env_build = EnvBuild(infile=temp_file.name, components=components)

            # Get regular entry value
            value = env_build.get_value("EXEROOT")
            self.assertEqual(value, "/path/to/exe")

            # Set regular entry value
            env_build.set_value("EXEROOT", "/new/path/to/exe")
            new_value = env_build.get_value("EXEROOT")
            self.assertEqual(new_value, "/new/path/to/exe")

    def test_env_build_validate_exeroot_not_caseroot(self):
        """Test that EXEROOT cannot be set to CASEROOT."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_file = Path(tmpdir) / "env_build.xml"
            temp_file.write_text(ENV_BUILD_BASE)

            env_build = EnvBuild(case_root=tmpdir, infile=str(temp_file))

            # Attempting to set EXEROOT to CASEROOT should raise an error
            with self.assertRaises(CIMEError):
                env_build.set_value("EXEROOT", tmpdir)

    def test_env_build_components_preserved_across_operations(self):
        """Test that _components is preserved across multiple operations."""
        with ExitStack() as stack:
            temp_file = _open_temp_file(stack, ENV_BUILD_BASE)
            components = ["atm", "lnd", "ocn"]
            env_build = EnvBuild(infile=temp_file.name, components=components)

            # Perform multiple operations
            env_build.get_value("COMP_BOOST_OPTION", attribute={"compclass": "atm"})
            env_build.set_value("COMP_BOOST_OPTION", "new_value")
            env_build.get_value("EXEROOT")

            # Verify _components is still set
            self.assertEqual(env_build._components, components)

    def test_env_build_empty_components_list(self):
        """Test that EnvBuild handles empty components list."""
        with ExitStack() as stack:
            temp_file = _open_temp_file(stack, ENV_BUILD_BASE)
            env_build = EnvBuild(infile=temp_file.name, components=[])

            # Verify _components is empty list
            self.assertEqual(env_build._components, [])

    def test_env_build_get_value_without_compclass_attribute(self):
        """Test getting value without compclass when components exist."""
        with ExitStack() as stack:
            temp_file = _open_temp_file(stack, ENV_BUILD_BASE)
            components = ["atm", "lnd", "ocn"]
            env_build = EnvBuild(infile=temp_file.name, components=components)

            # Get regular (non-compclass) entry value
            value = env_build.get_value("EXEROOT")
            self.assertEqual(value, "/path/to/exe")


if __name__ == "__main__":
    unittest.main()
