#!/usr/bin/env python3

import unittest
import tempfile
from unittest import mock

from CIME import utils
from CIME.XML.env_mach_specific import EnvMachSpecific

# pylint: disable=unused-argument


class TestXMLEnvMachSpecific(unittest.TestCase):
    def test_aprun_get_args(self):
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(
                b"""<?xml version="1.0"?>
<file id="env_mach_specific.xml" version="2.0">
  <header>
    These variables control the machine dependent environment including
    the paths to compilers and libraries external to cime such as netcdf,
    environment variables for use in the running job should also be set here.
    </header>
  <group id="compliant_values">
    <entry id="run_exe" value="${EXEROOT}/e3sm.exe ">
      <type>char</type>
      <desc>executable name</desc>
    </entry>
    <entry id="run_misc_suffix" value=" &gt;&gt; e3sm.log.$LID 2&gt;&amp;1 ">
      <type>char</type>
      <desc>redirect for job output</desc>
    </entry>
  </group>
  <module_system type="none"/>
  <environment_variables>
    <env name="OMPI_ALLOW_RUN_AS_ROOT">1</env>
    <env name="OMPI_ALLOW_RUN_AS_ROOT_CONFIRM">1</env>
  </environment_variables>
  <mpirun mpilib="openmpi">
    <aprun_mode>override</aprun_mode>
    <executable>aprun</executable>
    <arguments>
      <arg name="default_per">-j 10</arg>
      <arg name="ntasks" position="global">-n {{ total_tasks }}</arg>
      <arg name="oversubscribe" position="per">--oversubscribe</arg>
    </arguments>
  </mpirun>
</file>
"""
            )
            temp.seek(0)

            mach_specific = EnvMachSpecific(infile=temp.name)

            attribs = {"compiler": "gnu", "mpilib": "openmpi", "threaded": False}

            case = mock.MagicMock()

            type(case).total_tasks = mock.PropertyMock(return_value=4)

            extra_args = mach_specific.get_aprun_args(case, attribs, "case.run")

            expected_args = {
                "-j 10": {"position": "per"},
                "--oversubscribe": {"position": "per"},
                "-n 4": {"position": "global"},
            }

            assert extra_args == expected_args

    def test_get_aprun_mode_not_valid(self):
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(
                b"""<?xml version="1.0"?>
<file id="env_mach_specific.xml" version="2.0">
  <header>
    These variables control the machine dependent environment including
    the paths to compilers and libraries external to cime such as netcdf,
    environment variables for use in the running job should also be set here.
    </header>
  <group id="compliant_values">
    <entry id="run_exe" value="${EXEROOT}/e3sm.exe ">
      <type>char</type>
      <desc>executable name</desc>
    </entry>
    <entry id="run_misc_suffix" value=" &gt;&gt; e3sm.log.$LID 2&gt;&amp;1 ">
      <type>char</type>
      <desc>redirect for job output</desc>
    </entry>
  </group>
  <module_system type="none"/>
  <environment_variables>
    <env name="OMPI_ALLOW_RUN_AS_ROOT">1</env>
    <env name="OMPI_ALLOW_RUN_AS_ROOT_CONFIRM">1</env>
  </environment_variables>
  <mpirun mpilib="openmpi">
    <aprun_mode>custom</aprun_mode>
    <executable>aprun</executable>
    <arguments>
      <arg name="ntasks">-n {{ total_tasks }}</arg>
      <arg name="oversubscribe">--oversubscribe</arg>
    </arguments>
  </mpirun>
</file>
"""
            )
            temp.seek(0)

            mach_specific = EnvMachSpecific(infile=temp.name)

            attribs = {"compiler": "gnu", "mpilib": "openmpi", "threaded": False}

            with self.assertRaises(utils.CIMEError) as e:
                mach_specific.get_aprun_mode(attribs)

            assert (
                str(e.exception)
                == "ERROR: Value 'custom' for \"aprun_mode\" is not valid, options are 'ignore, default, override'"
            )

    def test_get_aprun_mode_user_defined(self):
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(
                b"""<?xml version="1.0"?>
<file id="env_mach_specific.xml" version="2.0">
  <header>
    These variables control the machine dependent environment including
    the paths to compilers and libraries external to cime such as netcdf,
    environment variables for use in the running job should also be set here.
    </header>
  <group id="compliant_values">
    <entry id="run_exe" value="${EXEROOT}/e3sm.exe ">
      <type>char</type>
      <desc>executable name</desc>
    </entry>
    <entry id="run_misc_suffix" value=" &gt;&gt; e3sm.log.$LID 2&gt;&amp;1 ">
      <type>char</type>
      <desc>redirect for job output</desc>
    </entry>
  </group>
  <module_system type="none"/>
  <environment_variables>
    <env name="OMPI_ALLOW_RUN_AS_ROOT">1</env>
    <env name="OMPI_ALLOW_RUN_AS_ROOT_CONFIRM">1</env>
  </environment_variables>
  <mpirun mpilib="openmpi">
    <aprun_mode>default</aprun_mode>
    <executable>aprun</executable>
    <arguments>
      <arg name="ntasks">-n {{ total_tasks }}</arg>
      <arg name="oversubscribe">--oversubscribe</arg>
    </arguments>
  </mpirun>
</file>
"""
            )
            temp.seek(0)

            mach_specific = EnvMachSpecific(infile=temp.name)

            attribs = {"compiler": "gnu", "mpilib": "openmpi", "threaded": False}

            aprun_mode = mach_specific.get_aprun_mode(attribs)

            assert aprun_mode == "default"

    def test_get_aprun_mode_default(self):
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(
                b"""<?xml version="1.0"?>
<file id="env_mach_specific.xml" version="2.0">
  <header>
    These variables control the machine dependent environment including
    the paths to compilers and libraries external to cime such as netcdf,
    environment variables for use in the running job should also be set here.
    </header>
  <group id="compliant_values">
    <entry id="run_exe" value="${EXEROOT}/e3sm.exe ">
      <type>char</type>
      <desc>executable name</desc>
    </entry>
    <entry id="run_misc_suffix" value=" &gt;&gt; e3sm.log.$LID 2&gt;&amp;1 ">
      <type>char</type>
      <desc>redirect for job output</desc>
    </entry>
  </group>
  <module_system type="none"/>
  <environment_variables>
    <env name="OMPI_ALLOW_RUN_AS_ROOT">1</env>
    <env name="OMPI_ALLOW_RUN_AS_ROOT_CONFIRM">1</env>
  </environment_variables>
  <mpirun mpilib="openmpi">
    <executable>aprun</executable>
    <arguments>
      <arg name="ntasks">-n {{ total_tasks }}</arg>
      <arg name="oversubscribe">--oversubscribe</arg>
    </arguments>
  </mpirun>
</file>
"""
            )
            temp.seek(0)

            mach_specific = EnvMachSpecific(infile=temp.name)

            attribs = {"compiler": "gnu", "mpilib": "openmpi", "threaded": False}

            aprun_mode = mach_specific.get_aprun_mode(attribs)

            assert aprun_mode == "default"

    def test_find_best_mpirun_match(self):
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(
                b"""<?xml version="1.0"?>
<file id="env_mach_specific.xml" version="2.0">
  <header>
    These variables control the machine dependent environment including
    the paths to compilers and libraries external to cime such as netcdf,
    environment variables for use in the running job should also be set here.
    </header>
  <group id="compliant_values">
    <entry id="run_exe" value="${EXEROOT}/e3sm.exe ">
      <type>char</type>
      <desc>executable name</desc>
    </entry>
    <entry id="run_misc_suffix" value=" &gt;&gt; e3sm.log.$LID 2&gt;&amp;1 ">
      <type>char</type>
      <desc>redirect for job output</desc>
    </entry>
  </group>
  <module_system type="none"/>
  <environment_variables>
    <env name="OMPI_ALLOW_RUN_AS_ROOT">1</env>
    <env name="OMPI_ALLOW_RUN_AS_ROOT_CONFIRM">1</env>
  </environment_variables>
  <mpirun mpilib="openmpi">
    <executable>aprun</executable>
    <arguments>
      <arg name="ntasks">-n {{ total_tasks }}</arg>
      <arg name="oversubscribe">--oversubscribe</arg>
    </arguments>
  </mpirun>
  <mpirun mpilib="openmpi" compiler="gnu">
    <executable>srun</executable>
  </mpirun>
</file>
"""
            )
            temp.seek(0)

            mach_specific = EnvMachSpecific(infile=temp.name)

            mock_case = mock.MagicMock()

            type(mock_case).total_tasks = mock.PropertyMock(return_value=4)

            attribs = {"compiler": "gnu", "mpilib": "openmpi", "threaded": False}

            executable, args, run_exe, run_misc_suffix = mach_specific.get_mpirun(
                mock_case, attribs, "case.run"
            )

            assert executable == "srun"
            assert args == []
            assert run_exe is None
            assert run_misc_suffix is None

    def test_get_mpirun(self):
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(
                b"""<?xml version="1.0"?>
<file id="env_mach_specific.xml" version="2.0">
  <header>
    These variables control the machine dependent environment including
    the paths to compilers and libraries external to cime such as netcdf,
    environment variables for use in the running job should also be set here.
    </header>
  <group id="compliant_values">
    <entry id="run_exe" value="${EXEROOT}/e3sm.exe ">
      <type>char</type>
      <desc>executable name</desc>
    </entry>
    <entry id="run_misc_suffix" value=" &gt;&gt; e3sm.log.$LID 2&gt;&amp;1 ">
      <type>char</type>
      <desc>redirect for job output</desc>
    </entry>
  </group>
  <module_system type="none"/>
  <environment_variables>
    <env name="OMPI_ALLOW_RUN_AS_ROOT">1</env>
    <env name="OMPI_ALLOW_RUN_AS_ROOT_CONFIRM">1</env>
  </environment_variables>
  <mpirun mpilib="openmpi">
    <executable>aprun</executable>
    <arguments>
      <arg name="ntasks">-n {{ total_tasks }}</arg>
      <arg name="oversubscribe">--oversubscribe</arg>
    </arguments>
  </mpirun>
</file>
"""
            )
            temp.seek(0)

            mach_specific = EnvMachSpecific(infile=temp.name)

            mock_case = mock.MagicMock()

            type(mock_case).total_tasks = mock.PropertyMock(return_value=4)

            attribs = {"compiler": "gnu", "mpilib": "openmpi", "threaded": False}

            executable, args, run_exe, run_misc_suffix = mach_specific.get_mpirun(
                mock_case, attribs, "case.run"
            )

            assert executable == "aprun"
            assert args == ["-n 4", "--oversubscribe"]
            assert run_exe is None
            assert run_misc_suffix is None

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
