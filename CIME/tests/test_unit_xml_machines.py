import io
import os
import re
import unittest
from contextlib import redirect_stdout

from CIME.XML.machines import Machines

MACHINE_TEST_XML = """<config_machines version="2.0">
  <machine MACH="default">
    <DESC>Some default machine definition</DESC>
    <OS>ubuntu</OS>
    <COMPILERS>gnu,intel</COMPILERS>
    <MPILIBS>mpi-serial</MPILIBS>
    <PROJECT>custom</PROJECT>
    <SAVE_TIMING_DIR>/data/timings</SAVE_TIMING_DIR>
    <SAVE_TIMING_DIR_PROJECTS>testing</SAVE_TIMING_DIR_PROJECTS>
    <CIME_OUTPUT_ROOT>/data/scratch</CIME_OUTPUT_ROOT>
    <DIN_LOC_ROOT>/data/inputdata</DIN_LOC_ROOT>
    <DIN_LOC_ROOT_CLMFORC>/data/inputdata/atm/datm7</DIN_LOC_ROOT_CLMFORC>
    <DOUT_S_ROOT>$CIME_OUTPUT_ROOT/archive/$CASE</DOUT_S_ROOT>
    <BASELINE_ROOT>/data/baselines/$COMPILER</BASELINE_ROOT>
    <CCSM_CPRNC>/data/tools/cprnc</CCSM_CPRNC>
    <GMAKE_J>8</GMAKE_J>
    <TESTS>e3sm_developer</TESTS>
    <NTEST_PARALLEL_JOBS>4</NTEST_PARALLEL_JOBS>
    <BATCH_SYSTEM>slurm</BATCH_SYSTEM>
    <SUPPORTED_BY>developers</SUPPORTED_BY>
    <MAX_TASKS_PER_NODE>8</MAX_TASKS_PER_NODE>
    <MAX_MPITASKS_PER_NODE>8</MAX_MPITASKS_PER_NODE>
    <PROJECT_REQUIRED>FALSE</PROJECT_REQUIRED>
    <mpirun mpilib="default">
      <executable>srun</executable>
      <arguments>
        <arg name="num_tasks">-n {{ total_tasks }} -N {{ num_nodes }} --kill-on-bad-exit </arg>
        <arg name="thread_count">-c $SHELL{echo 128/ {{ tasks_per_node }} |bc}</arg>
        <arg name="binding"> $SHELL{if [ 128 -ge `./xmlquery --value MAX_MPITASKS_PER_NODE` ]; then echo "--cpu_bind=cores"; else echo "--cpu_bind=threads";fi;} </arg>
        <arg name="placement">-m plane={{ tasks_per_node }}</arg>
      </arguments>
    </mpirun>
    <module_system type="module">
      <init_path lang="perl">/opt/ubuntu/pe/modules/default/init/perl.pm</init_path>
      <init_path lang="python">/opt/ubuntu/pe/modules/default/init/python.py</init_path>
      <init_path lang="sh">/opt/ubuntu/pe/modules/default/init/sh</init_path>
      <init_path lang="csh">/opt/ubuntu/pe/modules/default/init/csh</init_path>
      <cmd_path lang="perl">/opt/ubuntu/pe/modules/default/bin/modulecmd perl</cmd_path>
      <cmd_path lang="python">/opt/ubuntu/pe/modules/default/bin/modulecmd python</cmd_path>
      <cmd_path lang="sh">module</cmd_path>
      <cmd_path lang="csh">module</cmd_path>
      <modules>
        <command name="unload">ubuntupe</command>
        <command name="unload">ubuntu-mpich</command>
        <command name="unload">ubuntu-parallel-netcdf</command>
        <command name="unload">ubuntu-hdf5-parallel</command>
        <command name="unload">ubuntu-hdf5</command>
        <command name="unload">ubuntu-netcdf</command>
        <command name="unload">ubuntu-netcdf-hdf5parallel</command>
        <command name="load">ubuntupe/2.7.15</command>
      </modules>
      <modules compiler="gnu">
        <command name="unload">PrgEnv-ubuntu</command>
        <command name="unload">PrgEnv-gnu</command>
        <command name="load">PrgEnv-gnu/8.3.3</command>
        <command name="swap">gcc/12.1.0</command>
      </modules>
      <modules>
        <command name="load">ubuntu-mpich/8.1.16</command>
        <command name="load">ubuntu-hdf5-parallel/1.12.1.3</command>
        <command name="load">ubuntu-netcdf-hdf5parallel/4.8.1.3</command>
        <command name="load">ubuntu-parallel-netcdf/1.12.2.3</command>
      </modules>
    </module_system>

    <RUNDIR>$CIME_OUTPUT_ROOT/$CASE/run</RUNDIR>
    <EXEROOT>$CIME_OUTPUT_ROOT/$CASE/bld</EXEROOT>
    <TEST_TPUT_TOLERANCE>0.1</TEST_TPUT_TOLERANCE>
    <MAX_GB_OLD_TEST_DATA>1000</MAX_GB_OLD_TEST_DATA>
    <environment_variables>
      <env name="PERL5LIB">/usr/lib/perl5/5.26.2</env>
      <env name="NETCDF_C_PATH">/opt/ubuntu/pe/netcdf-hdf5parallel/4.8.1.3/gnu/9.1/</env>
      <env name="NETCDF_FORTRAN_PATH">/opt/ubuntu/pe/netcdf-hdf5parallel/4.8.1.3/gnu/9.1/</env>
      <env name="PNETCDF_PATH">$SHELL{dirname $(dirname $(which pnetcdf_version))}</env>
    </environment_variables>
    <environment_variables BUILD_THREADED="TRUE">
      <env name="OMP_STACKSIZE">128M</env>
    </environment_variables>
    <environment_variables BUILD_THREADED="TRUE" compiler="gnu">
      <env name="OMP_PLACES">cores</env>
    </environment_variables>
  </machine>
  <machine MACH="default-no-batch">
    <DESC>Some default machine definition</DESC>
    <OS>ubuntu</OS>
    <COMPILERS>gnu,intel</COMPILERS>
    <MPILIBS>mpi-serial</MPILIBS>
    <PROJECT>custom</PROJECT>
    <SAVE_TIMING_DIR>/data/timings</SAVE_TIMING_DIR>
    <SAVE_TIMING_DIR_PROJECTS>testing</SAVE_TIMING_DIR_PROJECTS>
    <CIME_OUTPUT_ROOT>/data/scratch</CIME_OUTPUT_ROOT>
    <DIN_LOC_ROOT>/data/inputdata</DIN_LOC_ROOT>
    <DIN_LOC_ROOT_CLMFORC>/data/inputdata/atm/datm7</DIN_LOC_ROOT_CLMFORC>
    <DOUT_S_ROOT>$CIME_OUTPUT_ROOT/archive/$CASE</DOUT_S_ROOT>
    <BASELINE_ROOT>/data/baselines/$COMPILER</BASELINE_ROOT>
    <CCSM_CPRNC>/data/tools/cprnc</CCSM_CPRNC>
    <GMAKE_J>8</GMAKE_J>
    <TESTS>e3sm_developer</TESTS>
    <NTEST_PARALLEL_JOBS>4</NTEST_PARALLEL_JOBS>
    <BATCH_SYSTEM>none</BATCH_SYSTEM>
    <SUPPORTED_BY>developers</SUPPORTED_BY>
    <MAX_TASKS_PER_NODE>8</MAX_TASKS_PER_NODE>
    <MAX_MPITASKS_PER_NODE>8</MAX_MPITASKS_PER_NODE>
    <PROJECT_REQUIRED>FALSE</PROJECT_REQUIRED>
    <mpirun mpilib="default">
      <executable>srun</executable>
      <arguments>
        <arg name="num_tasks">-n {{ total_tasks }} -N {{ num_nodes }} --kill-on-bad-exit </arg>
        <arg name="thread_count">-c $SHELL{echo 128/ {{ tasks_per_node }} |bc}</arg>
        <arg name="binding"> $SHELL{if [ 128 -ge `./xmlquery --value MAX_MPITASKS_PER_NODE` ]; then echo "--cpu_bind=cores"; else echo "--cpu_bind=threads";fi;} </arg>
        <arg name="placement">-m plane={{ tasks_per_node }}</arg>
      </arguments>
    </mpirun>
    <RUNDIR>$CIME_OUTPUT_ROOT/$CASE/run</RUNDIR>
    <EXEROOT>$CIME_OUTPUT_ROOT/$CASE/bld</EXEROOT>
    <TEST_TPUT_TOLERANCE>0.1</TEST_TPUT_TOLERANCE>
    <MAX_GB_OLD_TEST_DATA>1000</MAX_GB_OLD_TEST_DATA>
    <environment_variables>
      <env name="PERL5LIB">/usr/lib/perl5/5.26.2</env>
      <env name="NETCDF_C_PATH">/opt/ubuntu/pe/netcdf-hdf5parallel/4.8.1.3/gnu/9.1/</env>
      <env name="NETCDF_FORTRAN_PATH">/opt/ubuntu/pe/netcdf-hdf5parallel/4.8.1.3/gnu/9.1/</env>
      <env name="PNETCDF_PATH">$SHELL{dirname $(dirname $(which pnetcdf_version))}</env>
    </environment_variables>
    <environment_variables BUILD_THREADED="TRUE">
      <env name="OMP_STACKSIZE">128M</env>
    </environment_variables>
    <environment_variables BUILD_THREADED="TRUE" compiler="gnu">
      <env name="OMP_PLACES">cores</env>
    </environment_variables>
  </machine>
  <machine MACH="multi-compiler">
    <DESC>Some default machine definition</DESC>
    <OS>ubuntu</OS>
    <COMPILERS>gnu,gnugpu,intel</COMPILERS>
    <MPILIBS>mpi-serial,openmpi,mpich2</MPILIBS>
    <MPILIBS compiler="intel">impi,mpi-serial</MPILIBS>
    <GMAKE_J>8</GMAKE_J>
    <GMAKE_J mpilib="openmpi">16</GMAKE_J>
    <PROJECT>custom</PROJECT>
    <SAVE_TIMING_DIR>/data/timings</SAVE_TIMING_DIR>
    <SAVE_TIMING_DIR_PROJECTS>testing</SAVE_TIMING_DIR_PROJECTS>
    <CIME_OUTPUT_ROOT>/data/scratch</CIME_OUTPUT_ROOT>
    <DIN_LOC_ROOT>/data/inputdata</DIN_LOC_ROOT>
    <DIN_LOC_ROOT_CLMFORC>/data/inputdata/atm/datm7</DIN_LOC_ROOT_CLMFORC>
    <DOUT_S_ROOT>$CIME_OUTPUT_ROOT/archive/$CASE</DOUT_S_ROOT>
    <BASELINE_ROOT>/data/baselines/$COMPILER</BASELINE_ROOT>
    <CCSM_CPRNC>/data/tools/cprnc</CCSM_CPRNC>
    <TESTS>e3sm_developer</TESTS>
    <NTEST_PARALLEL_JOBS>4</NTEST_PARALLEL_JOBS>
    <BATCH_SYSTEM>slurm</BATCH_SYSTEM>
    <SUPPORTED_BY>developers</SUPPORTED_BY>
    <MAX_TASKS_PER_NODE>8</MAX_TASKS_PER_NODE>
    <MAX_MPITASKS_PER_NODE>8</MAX_MPITASKS_PER_NODE>
    <PROJECT_REQUIRED>FALSE</PROJECT_REQUIRED>
    <mpirun mpilib="default">
      <executable>srun</executable>
      <arguments>
        <arg name="num_tasks">-n {{ total_tasks }} -N {{ num_nodes }} --kill-on-bad-exit </arg>
        <arg name="thread_count">-c $SHELL{echo 128/ {{ tasks_per_node }} |bc}</arg>
        <arg name="binding"> $SHELL{if [ 128 -ge `./xmlquery --value MAX_MPITASKS_PER_NODE` ]; then echo "--cpu_bind=cores"; else echo "--cpu_bind=threads";fi;} </arg>
        <arg name="placement">-m plane={{ tasks_per_node }}</arg>
      </arguments>
    </mpirun>
    <module_system type="module">
      <init_path lang="perl">/opt/ubuntu/pe/modules/default/init/perl.pm</init_path>
      <init_path lang="python">/opt/ubuntu/pe/modules/default/init/python.py</init_path>
      <init_path lang="sh">/opt/ubuntu/pe/modules/default/init/sh</init_path>
      <init_path lang="csh">/opt/ubuntu/pe/modules/default/init/csh</init_path>
      <cmd_path lang="perl">/opt/ubuntu/pe/modules/default/bin/modulecmd perl</cmd_path>
      <cmd_path lang="python">/opt/ubuntu/pe/modules/default/bin/modulecmd python</cmd_path>
      <cmd_path lang="sh">module</cmd_path>
      <cmd_path lang="csh">module</cmd_path>
      <modules>
        <command name="purge"/>
        <command name="load">ubuntupe/2.7.15</command>
      </modules>
      <modules DEBUG="TRUE">
        <command name="load">debug</command>
      </modules>
      <modules compiler="intel">>
        <command name="load">PrgEnv-intel/8.3.3</command>
      </modules>
      <modules compiler="gnu">
        <command name="load">PrgEnv-gnu/8.3.3</command>
      </modules>
      <modules compiler="gnu.*">
        <command name="load">PrgEnv-gnu/8.3.3</command>
        <command name="load">PrgEnv-gnugpu/8.3.3</command>
      </modules>
      <modules compiler="gnugpu">>
        <command name="load">PrgEnv-gnugpu/8.3.3</command>
      </modules>
      <modules>
        <command name="load">ubuntu-mpich/8.1.16</command>
      </modules>
    </module_system>

    <RUNDIR>$CIME_OUTPUT_ROOT/$CASE/run</RUNDIR>
    <EXEROOT>$CIME_OUTPUT_ROOT/$CASE/bld</EXEROOT>
    <TEST_TPUT_TOLERANCE>0.1</TEST_TPUT_TOLERANCE>
    <MAX_GB_OLD_TEST_DATA>1000</MAX_GB_OLD_TEST_DATA>
    <environment_variables>
      <env name="PERL5LIB">/usr/lib/perl5/5.26.2</env>
      <env name="NETCDF_C_PATH">/opt/ubuntu/pe/netcdf-hdf5parallel/4.8.1.3/gnu/9.1/</env>
      <env name="NETCDF_FORTRAN_PATH">/opt/ubuntu/pe/netcdf-hdf5parallel/4.8.1.3/gnu/9.1/</env>
      <env name="PNETCDF_PATH">$SHELL{dirname $(dirname $(which pnetcdf_version))}</env>
    </environment_variables>
    <environment_variables BUILD_THREADED="TRUE">
      <env name="OMP_STACKSIZE">128M</env>
    </environment_variables>
    <environment_variables BUILD_THREADED="TRUE" compiler="gnu">
      <env name="OMP_PLACES">cores</env>
    </environment_variables>
    <environment_variables BUILD_THREADED="TRUE" compiler="gnu.*">
      <env name="OMP_PLACES">cores</env>
    </environment_variables>
    <environment_variables BUILD_THREADED="TRUE" compiler="gnugpu">
      <env name="OMP_PLACES">gpu</env>
    </environment_variables>
    <environment_variables BUILD_THREADED="TRUE" compiler="intel">
      <env name="OMP_STACKSIZE">128M</env>
    </environment_variables>
  </machine>
</config_machines>
"""


class TestUnitXMLMachines(unittest.TestCase):
    def setUp(self):
        Machines._FILEMAP = {}
        # read_only=False for github testing
        # MACHINE IS SET BELOW TO USE DEFINITION IN "MACHINE_TEST_XML"
        self.machine = Machines()

        self.machine.read_fd(io.StringIO(MACHINE_TEST_XML))

    def test_get_resolved_environment_variable(self):
        self.machine.set_machine("multi-compiler")

        assert os.environ["HOME"] == self.machine._get_resolved_environment_variable(
            "$ENV{HOME}"
        )
        assert "" == self.machine._get_resolved_environment_variable("")

    def test_filter_children_by_compiler(self):
        self.machine.set_machine("multi-compiler")

        module_system_node = self.machine.get_child("module_system")

        def command_formatter(x):
            return (
                f"{x.attrib['name']}"
                if x.text is None
                else f"{x.attrib['name']} {x.text}"
            )

        nodes = list(
            self.machine._filter_children_by_compiler(
                "modules", "command", "intel", command_formatter, module_system_node
            )
        )

        assert len(nodes) == 4
        assert nodes[0] == ("", ["purge", "load ubuntupe/2.7.15"])
        assert nodes[1] == ("DEBUG='TRUE'", ["load debug"])
        assert nodes[2] == ("", ["load PrgEnv-intel/8.3.3"])
        assert nodes[3] == ("", ["load ubuntu-mpich/8.1.16"])

        nodes = list(
            self.machine._filter_children_by_compiler(
                "modules", "command", "gnugpu", command_formatter, module_system_node
            )
        )

        assert len(nodes) == 6
        assert nodes[0] == ("", ["purge", "load ubuntupe/2.7.15"])
        assert nodes[1] == ("DEBUG='TRUE'", ["load debug"])
        assert nodes[2] == ("", ["load PrgEnv-gnu/8.3.3"])
        assert nodes[3] == ("", ["load PrgEnv-gnu/8.3.3", "load PrgEnv-gnugpu/8.3.3"])
        assert nodes[4] == ("", ["load PrgEnv-gnugpu/8.3.3"])
        assert nodes[5] == ("", ["load ubuntu-mpich/8.1.16"])

    def test_print_values(self):
        self.machine.set_machine("default")

        with io.StringIO() as buffer, redirect_stdout(buffer):
            self.machine.print_values()

            output = buffer.getvalue()

        assert "ubuntu" in output
        assert "gnu,intel" in output
        assert "mpi-serial" in output
        assert "unload ubuntupe" not in output

    def test_print_values_details(self):
        self.machine.set_machine("default")

        with io.StringIO() as buffer, redirect_stdout(buffer):
            self.machine.print_values("intel")

            output = buffer.getvalue()

        assert "ubuntu" in output
        assert "gnu,intel" in output
        assert "mpi-serial" in output
        assert "unload ubuntupe" in output
        assert "unload PrgEnv-ubuntu" not in output
        assert "load ubuntu-mpich/8.1.16" in output
        assert "(with BUILD_THREADED='TRUE')" in output
        assert "PERL5LIB: /usr/lib/perl5/5.26.2" in output
        assert "OMP_PLACES: cores" not in output

    def test_has_batch_system(self):
        self.machine.set_machine("default")

        assert self.machine.has_batch_system()

        self.machine.set_machine("default-no-batch")

        assert not self.machine.has_batch_system()

    def test_is_valid_MPIlib(self):
        self.machine.set_machine("default")

        assert self.machine.is_valid_MPIlib("mpi-serial")

        assert not self.machine.is_valid_MPIlib("mpi-bogus")

    def test_is_valid_compiler(self):
        self.machine.set_machine("default")

        assert self.machine.is_valid_compiler("gnu")

        assert not self.machine.is_valid_compiler("bogus")

    def test_get_value_without_compiler_returns_generic(self):
        """get_value returns the generic value when no compiler is set in custom_settings."""
        self.machine.set_machine("multi-compiler")

        assert self.machine.get_value("MPILIBS") == "mpi-serial,openmpi,mpich2"

    def test_get_value_with_compiler_returns_compiler_specific(self):
        """get_value auto-injects compiler from custom_settings and returns its specific value."""
        self.machine.set_machine("multi-compiler")
        self.machine.set_value("COMPILER", "intel")

        assert self.machine.get_value("MPILIBS") == "impi,mpi-serial"

    def test_get_value_compiler_falls_back_to_generic_when_no_match(self):
        """get_value falls back to the generic value when no compiler-specific node exists."""
        self.machine.set_machine("multi-compiler")
        self.machine.set_value("COMPILER", "gnu")

        # No <MPILIBS compiler="gnu"> node, so the generic value is returned.
        assert self.machine.get_value("MPILIBS") == "mpi-serial,openmpi,mpich2"

    def test_get_value_with_compiler_and_mpilib_uses_priority_order(self):
        """With both COMPILER and MPILIB set, compiler+mpilib is most specific, then compiler, then mpilib."""
        self.machine.set_machine("multi-compiler")
        self.machine.set_value("COMPILER", "intel")
        self.machine.set_value("MPILIB", "openmpi")

        # compiler-only match found for MPILIBS before mpilib-only is tried
        assert self.machine.get_value("MPILIBS") == "impi,mpi-serial"
        # no compiler-only GMAKE_J, so mpilib-only match is used
        assert self.machine.get_value("GMAKE_J") == 16

    def test_get_value_with_mpilib_returns_mpilib_specific(self):
        """get_value auto-injects mpilib from custom_settings and returns its specific value."""
        self.machine.set_machine("multi-compiler")
        self.machine.set_value("MPILIB", "openmpi")

        assert self.machine.get_value("GMAKE_J") == 16

    def test_get_value_mpilib_falls_back_to_generic_when_no_match(self):
        """get_value falls back to the generic value when no mpilib-specific node exists."""
        self.machine.set_machine("multi-compiler")
        self.machine.set_value("MPILIB", "mpi-serial")

        # No <GMAKE_J mpilib="mpi-serial"> node, so the generic value is returned.
        assert self.machine.get_value("GMAKE_J") == 8
