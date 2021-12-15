#!/usr/bin/env python3

from CIME import utils
from CIME.tests import base
from CIME.tests import utils as test_utils
from CIME.XML.compilers import Compilers


class TestCMakeMacros(base.BaseTestCase):
    """CMake macros tests.

    This class contains tests of the CMake output of Build.

    This class simply inherits all of the methods of TestMakeOutput, but changes
    the definition of xml_to_tester to create a CMakeTester instead.
    """

    def xml_to_tester(self, xml_string):
        """Helper that directly converts an XML string to a MakefileTester."""
        test_xml = test_utils._wrap_config_compilers_xml(xml_string)
        if self.NO_CMAKE:
            self.skipTest("Skipping cmake test")
        else:
            return test_utils.CMakeTester(
                self, test_utils.get_macros(self._maker, test_xml, "CMake")
            )

    def setUp(self):
        super().setUp()

        self.test_os = "SomeOS"
        self.test_machine = "mymachine"
        self.test_compiler = (
            self.MACHINE.get_default_compiler()
            if self.TEST_COMPILER is None
            else self.TEST_COMPILER
        )
        self.test_mpilib = (
            self.MACHINE.get_default_MPIlib(attributes={"compiler": self.test_compiler})
            if self.TEST_MPILIB is None
            else self.TEST_MPILIB
        )

        self._maker = Compilers(
            test_utils.MockMachines(self.test_machine, self.test_os), version=2.0
        )

    def test_generic_item(self):
        """The macro writer can write out a single generic item."""
        xml_string = "<compiler><SUPPORTS_CXX>FALSE</SUPPORTS_CXX></compiler>"
        tester = self.xml_to_tester(xml_string)
        tester.assert_variable_equals("SUPPORTS_CXX", "FALSE")

    def test_machine_specific_item(self):
        """The macro writer can pick out a machine-specific item."""
        xml1 = """<compiler MACH="{}"><SUPPORTS_CXX>TRUE</SUPPORTS_CXX></compiler>""".format(
            self.test_machine
        )
        xml2 = """<compiler><SUPPORTS_CXX>FALSE</SUPPORTS_CXX></compiler>"""
        tester = self.xml_to_tester(xml1 + xml2)
        tester.assert_variable_equals("SUPPORTS_CXX", "TRUE")
        # Do this a second time, but with elements in the reverse order, to
        # ensure that the code is not "cheating" by taking the first match.
        tester = self.xml_to_tester(xml2 + xml1)
        tester.assert_variable_equals("SUPPORTS_CXX", "TRUE")

    def test_ignore_non_match(self):
        """The macro writer ignores an entry with the wrong machine name."""
        xml1 = """<compiler MACH="bad"><SUPPORTS_CXX>TRUE</SUPPORTS_CXX></compiler>"""
        xml2 = """<compiler><SUPPORTS_CXX>FALSE</SUPPORTS_CXX></compiler>"""
        tester = self.xml_to_tester(xml1 + xml2)
        tester.assert_variable_equals("SUPPORTS_CXX", "FALSE")
        # Again, double-check that we don't just get lucky with the order.
        tester = self.xml_to_tester(xml2 + xml1)
        tester.assert_variable_equals("SUPPORTS_CXX", "FALSE")

    def test_os_specific_item(self):
        """The macro writer can pick out an OS-specific item."""
        xml1 = (
            """<compiler OS="{}"><SUPPORTS_CXX>TRUE</SUPPORTS_CXX></compiler>""".format(
                self.test_os
            )
        )
        xml2 = """<compiler><SUPPORTS_CXX>FALSE</SUPPORTS_CXX></compiler>"""
        tester = self.xml_to_tester(xml1 + xml2)
        tester.assert_variable_equals("SUPPORTS_CXX", "TRUE")
        tester = self.xml_to_tester(xml2 + xml1)
        tester.assert_variable_equals("SUPPORTS_CXX", "TRUE")

    def test_mach_other_compiler(self):
        """The macro writer compiler-specific logic works as expected."""
        xml1 = """<compiler COMPILER="{}"><CFLAGS><base>a b c</base></CFLAGS></compiler>""".format(
            self.test_compiler
        )
        xml2 = """<compiler MACH="{}" COMPILER="other"><CFLAGS><base>x y z</base></CFLAGS></compiler>""".format(
            self.test_machine
        )
        xml3 = """<compiler MACH="{}" COMPILER="{}"><CFLAGS><append>x y z</append></CFLAGS></compiler>""".format(
            self.test_machine, self.test_compiler
        )
        xml4 = """<compiler MACH="{}" COMPILER="{}"><CFLAGS><base>x y z</base></CFLAGS></compiler>""".format(
            self.test_machine, self.test_compiler
        )
        tester = self.xml_to_tester(xml1)
        tester.assert_variable_equals(
            "CFLAGS", "a b c", var={"COMPILER": self.test_compiler}
        )
        tester = self.xml_to_tester(xml1 + xml2)
        tester.assert_variable_equals(
            "CFLAGS", "a b c", var={"COMPILER": self.test_compiler}
        )
        tester = self.xml_to_tester(xml2 + xml1)
        tester.assert_variable_equals(
            "CFLAGS", "a b c", var={"COMPILER": self.test_compiler}
        )
        tester = self.xml_to_tester(xml1 + xml3)
        tester.assert_variable_equals(
            "CFLAGS", "a b c x y z", var={"COMPILER": self.test_compiler}
        )
        tester = self.xml_to_tester(xml1 + xml4)
        tester.assert_variable_equals(
            "CFLAGS", "x y z", var={"COMPILER": self.test_compiler}
        )
        tester = self.xml_to_tester(xml4 + xml1)
        tester.assert_variable_equals(
            "CFLAGS", "x y z", var={"COMPILER": self.test_compiler}
        )

    def test_mach_beats_os(self):
        """The macro writer chooses machine-specific over os-specific matches."""
        xml1 = """<compiler OS="{}"><SUPPORTS_CXX>FALSE</SUPPORTS_CXX></compiler>""".format(
            self.test_os
        )
        xml2 = """<compiler MACH="{}"><SUPPORTS_CXX>TRUE</SUPPORTS_CXX></compiler>""".format(
            self.test_machine
        )
        tester = self.xml_to_tester(xml1 + xml2)
        tester.assert_variable_equals("SUPPORTS_CXX", "TRUE")
        tester = self.xml_to_tester(xml2 + xml1)
        tester.assert_variable_equals("SUPPORTS_CXX", "TRUE")

    def test_mach_and_os_beats_mach(self):
        """The macro writer chooses the most-specific match possible."""
        xml1 = """<compiler MACH="{}"><SUPPORTS_CXX>FALSE</SUPPORTS_CXX></compiler>""".format(
            self.test_machine
        )
        xml2 = """<compiler MACH="{}" OS="{}"><SUPPORTS_CXX>TRUE</SUPPORTS_CXX></compiler>"""
        xml2 = xml2.format(self.test_machine, self.test_os)
        tester = self.xml_to_tester(xml1 + xml2)
        tester.assert_variable_equals("SUPPORTS_CXX", "TRUE")
        tester = self.xml_to_tester(xml2 + xml1)
        tester.assert_variable_equals("SUPPORTS_CXX", "TRUE")

    def test_build_time_attribute(self):
        """The macro writer writes conditionals for build-time choices."""
        xml1 = """<compiler><MPI_PATH MPILIB="mpich">/path/to/mpich</MPI_PATH></compiler>"""
        xml2 = """<compiler><MPI_PATH MPILIB="openmpi">/path/to/openmpi</MPI_PATH></compiler>"""
        xml3 = """<compiler><MPI_PATH>/path/to/default</MPI_PATH></compiler>"""
        tester = self.xml_to_tester(xml1 + xml2 + xml3)
        tester.assert_variable_equals("MPI_PATH", "/path/to/default")
        tester.assert_variable_equals(
            "MPI_PATH", "/path/to/mpich", var={"MPILIB": "mpich"}
        )
        tester.assert_variable_equals(
            "MPI_PATH", "/path/to/openmpi", var={"MPILIB": "openmpi"}
        )
        tester = self.xml_to_tester(xml3 + xml2 + xml1)
        tester.assert_variable_equals("MPI_PATH", "/path/to/default")
        tester.assert_variable_equals(
            "MPI_PATH", "/path/to/mpich", var={"MPILIB": "mpich"}
        )
        tester.assert_variable_equals(
            "MPI_PATH", "/path/to/openmpi", var={"MPILIB": "openmpi"}
        )

    def test_reject_duplicate_defaults(self):
        """The macro writer dies if given many defaults."""
        xml1 = """<compiler><MPI_PATH>/path/to/default</MPI_PATH></compiler>"""
        xml2 = """<compiler><MPI_PATH>/path/to/other_default</MPI_PATH></compiler>"""
        with self.assertRaisesRegex(
            utils.CIMEError,
            "Variable MPI_PATH is set ambiguously in config_compilers.xml.",
        ):
            self.xml_to_tester(xml1 + xml2)

    def test_reject_duplicates(self):
        """The macro writer dies if given many matches for a given configuration."""
        xml1 = """<compiler><MPI_PATH MPILIB="mpich">/path/to/mpich</MPI_PATH></compiler>"""
        xml2 = """<compiler><MPI_PATH MPILIB="mpich">/path/to/mpich2</MPI_PATH></compiler>"""
        with self.assertRaisesRegex(
            utils.CIMEError,
            "Variable MPI_PATH is set ambiguously in config_compilers.xml.",
        ):
            self.xml_to_tester(xml1 + xml2)

    def test_reject_ambiguous(self):
        """The macro writer dies if given an ambiguous set of matches."""
        xml1 = """<compiler><MPI_PATH MPILIB="mpich">/path/to/mpich</MPI_PATH></compiler>"""
        xml2 = """<compiler><MPI_PATH DEBUG="FALSE">/path/to/mpi-debug</MPI_PATH></compiler>"""
        with self.assertRaisesRegex(
            utils.CIMEError,
            "Variable MPI_PATH is set ambiguously in config_compilers.xml.",
        ):
            self.xml_to_tester(xml1 + xml2)

    def test_compiler_changeable_at_build_time(self):
        """The macro writer writes information for multiple compilers."""
        xml1 = """<compiler><SUPPORTS_CXX>FALSE</SUPPORTS_CXX></compiler>"""
        xml2 = (
            """<compiler COMPILER="gnu"><SUPPORTS_CXX>TRUE</SUPPORTS_CXX></compiler>"""
        )
        tester = self.xml_to_tester(xml1 + xml2)
        tester.assert_variable_equals("SUPPORTS_CXX", "TRUE", var={"COMPILER": "gnu"})
        tester.assert_variable_equals("SUPPORTS_CXX", "FALSE")

    def test_base_flags(self):
        """Test that we get "base" compiler flags."""
        xml1 = """<compiler><FFLAGS><base>-O2</base></FFLAGS></compiler>"""
        tester = self.xml_to_tester(xml1)
        tester.assert_variable_equals("FFLAGS", "-O2")

    def test_machine_specific_base_flags(self):
        """Test selection among base compiler flag sets based on machine."""
        xml1 = """<compiler><FFLAGS><base>-O2</base></FFLAGS></compiler>"""
        xml2 = """<compiler MACH="{}"><FFLAGS><base>-O3</base></FFLAGS></compiler>""".format(
            self.test_machine
        )
        tester = self.xml_to_tester(xml1 + xml2)
        tester.assert_variable_equals("FFLAGS", "-O3")

    def test_build_time_base_flags(self):
        """Test selection of base flags based on build-time attributes."""
        xml1 = """<compiler><FFLAGS><base>-O2</base></FFLAGS></compiler>"""
        xml2 = """<compiler><FFLAGS><base DEBUG="TRUE">-O3</base></FFLAGS></compiler>"""
        tester = self.xml_to_tester(xml1 + xml2)
        tester.assert_variable_equals("FFLAGS", "-O2")
        tester.assert_variable_equals("FFLAGS", "-O3", var={"DEBUG": "TRUE"})

    def test_build_time_base_flags_same_parent(self):
        """Test selection of base flags in the same parent element."""
        xml1 = """<base>-O2</base>"""
        xml2 = """<base DEBUG="TRUE">-O3</base>"""
        tester = self.xml_to_tester(
            "<compiler><FFLAGS>" + xml1 + xml2 + "</FFLAGS></compiler>"
        )
        tester.assert_variable_equals("FFLAGS", "-O2")
        tester.assert_variable_equals("FFLAGS", "-O3", var={"DEBUG": "TRUE"})
        # Check for order independence here, too.
        tester = self.xml_to_tester(
            "<compiler><FFLAGS>" + xml2 + xml1 + "</FFLAGS></compiler>"
        )
        tester.assert_variable_equals("FFLAGS", "-O2")
        tester.assert_variable_equals("FFLAGS", "-O3", var={"DEBUG": "TRUE"})

    def test_append_flags(self):
        """Test appending flags to a list."""
        xml1 = """<compiler><FFLAGS><base>-delicious</base></FFLAGS></compiler>"""
        xml2 = """<compiler><FFLAGS><append>-cake</append></FFLAGS></compiler>"""
        tester = self.xml_to_tester(xml1 + xml2)
        tester.assert_variable_equals("FFLAGS", "-delicious -cake")
        # Order independence, as usual.
        tester = self.xml_to_tester(xml2 + xml1)
        tester.assert_variable_equals("FFLAGS", "-delicious -cake")

    def test_machine_specific_append_flags(self):
        """Test appending flags that are either more or less machine-specific."""
        xml1 = """<compiler><FFLAGS><append>-delicious</append></FFLAGS></compiler>"""
        xml2 = """<compiler MACH="{}"><FFLAGS><append>-cake</append></FFLAGS></compiler>""".format(
            self.test_machine
        )
        tester = self.xml_to_tester(xml1 + xml2)
        tester.assert_variable_matches(
            "FFLAGS", "^(-delicious -cake|-cake -delicious)$"
        )

    def test_machine_specific_base_keeps_append_flags(self):
        """Test that machine-specific base flags don't override default append flags."""
        xml1 = """<compiler><FFLAGS><append>-delicious</append></FFLAGS></compiler>"""
        xml2 = """<compiler MACH="{}"><FFLAGS><base>-cake</base></FFLAGS></compiler>""".format(
            self.test_machine
        )
        tester = self.xml_to_tester(xml1 + xml2)
        tester.assert_variable_equals("FFLAGS", "-cake -delicious")
        tester = self.xml_to_tester(xml2 + xml1)
        tester.assert_variable_equals("FFLAGS", "-cake -delicious")

    def test_machine_specific_base_and_append_flags(self):
        """Test that machine-specific base flags coexist with machine-specific append flags."""
        xml1 = """<compiler MACH="{}"><FFLAGS><append>-delicious</append></FFLAGS></compiler>""".format(
            self.test_machine
        )
        xml2 = """<compiler MACH="{}"><FFLAGS><base>-cake</base></FFLAGS></compiler>""".format(
            self.test_machine
        )
        tester = self.xml_to_tester(xml1 + xml2)
        tester.assert_variable_equals("FFLAGS", "-cake -delicious")
        tester = self.xml_to_tester(xml2 + xml1)
        tester.assert_variable_equals("FFLAGS", "-cake -delicious")

    def test_append_flags_without_base(self):
        """Test appending flags to a value set before Macros is included."""
        xml1 = """<compiler><FFLAGS><append>-cake</append></FFLAGS></compiler>"""
        tester = self.xml_to_tester(xml1)
        tester.assert_variable_equals(
            "FFLAGS", "-delicious -cake", var={"FFLAGS": "-delicious"}
        )

    def test_build_time_append_flags(self):
        """Test build_time selection of compiler flags."""
        xml1 = """<compiler><FFLAGS><append>-cake</append></FFLAGS></compiler>"""
        xml2 = """<compiler><FFLAGS><append DEBUG="TRUE">-and-pie</append></FFLAGS></compiler>"""
        tester = self.xml_to_tester(xml1 + xml2)
        tester.assert_variable_equals("FFLAGS", "-cake")
        tester.assert_variable_matches(
            "FFLAGS", "^(-cake -and-pie|-and-pie -cake)$", var={"DEBUG": "TRUE"}
        )

    def test_environment_variable_insertion(self):
        """Test that ENV{..} inserts environment variables."""
        # DO it again with $ENV{} style
        xml1 = """<compiler><LDFLAGS><append>-L$ENV{NETCDF} -lnetcdf</append></LDFLAGS></compiler>"""
        tester = self.xml_to_tester(xml1)
        tester.assert_variable_equals(
            "LDFLAGS", "-L/path/to/netcdf -lnetcdf", env={"NETCDF": "/path/to/netcdf"}
        )

    def test_shell_command_insertion(self):
        """Test that $SHELL insert shell command output."""
        xml1 = """<compiler><FFLAGS><base>-O$SHELL{echo 2} -fast</base></FFLAGS></compiler>"""
        tester = self.xml_to_tester(xml1)
        tester.assert_variable_equals("FFLAGS", "-O2 -fast")

    def test_multiple_shell_commands(self):
        """Test that more than one $SHELL element can be used."""
        xml1 = """<compiler><FFLAGS><base>-O$SHELL{echo 2} -$SHELL{echo fast}</base></FFLAGS></compiler>"""
        tester = self.xml_to_tester(xml1)
        tester.assert_variable_equals("FFLAGS", "-O2 -fast")

    def test_env_and_shell_command(self):
        """Test that $ENV works inside $SHELL elements."""
        xml1 = """<compiler><FFLAGS><base>-O$SHELL{echo $ENV{OPT_LEVEL}} -fast</base></FFLAGS></compiler>"""
        tester = self.xml_to_tester(xml1)
        tester.assert_variable_equals("FFLAGS", "-O2 -fast", env={"OPT_LEVEL": "2"})

    def test_config_variable_insertion(self):
        """Test that $VAR insert variables from config_compilers."""
        # Construct an absurd chain of references just to sure that we don't
        # pass by accident, e.g. outputting things in the right order just due
        # to good luck in a hash somewhere.
        xml1 = """<MPI_LIB_NAME>stuff-${MPI_PATH}-stuff</MPI_LIB_NAME>"""
        xml2 = """<MPI_PATH>${MPICC}</MPI_PATH>"""
        xml3 = """<MPICC>${MPICXX}</MPICC>"""
        xml4 = """<MPICXX>${MPIFC}</MPICXX>"""
        xml5 = """<MPIFC>mpicc</MPIFC>"""
        tester = self.xml_to_tester(
            "<compiler>" + xml1 + xml2 + xml3 + xml4 + xml5 + "</compiler>"
        )
        tester.assert_variable_equals("MPI_LIB_NAME", "stuff-mpicc-stuff")

    def test_config_reject_self_references(self):
        """Test that $VAR self-references are rejected."""
        # This is a special case of the next test, which also checks circular
        # references.
        xml1 = """<MPI_LIB_NAME>${MPI_LIB_NAME}</MPI_LIB_NAME>"""
        err_msg = r".* has bad \$VAR references. Check for circular references or variables that are used in a \$VAR but not actually defined."
        with self.assertRaisesRegex(utils.CIMEError, err_msg):
            self.xml_to_tester("<compiler>" + xml1 + "</compiler>")

    def test_config_reject_cyclical_references(self):
        """Test that cyclical $VAR references are rejected."""
        xml1 = """<MPI_LIB_NAME>${MPI_PATH}</MPI_LIB_NAME>"""
        xml2 = """<MPI_PATH>${MPI_LIB_NAME}</MPI_PATH>"""
        err_msg = r".* has bad \$VAR references. Check for circular references or variables that are used in a \$VAR but not actually defined."
        with self.assertRaisesRegex(utils.CIMEError, err_msg):
            self.xml_to_tester("<compiler>" + xml1 + xml2 + "</compiler>")

    def test_variable_insertion_with_machine_specific_setting(self):
        """Test that machine-specific $VAR dependencies are correct."""
        xml1 = """<compiler><MPI_LIB_NAME>something</MPI_LIB_NAME></compiler>"""
        xml2 = """<compiler MACH="{}"><MPI_LIB_NAME>$MPI_PATH</MPI_LIB_NAME></compiler>""".format(
            self.test_machine
        )
        xml3 = """<compiler><MPI_PATH>${MPI_LIB_NAME}</MPI_PATH></compiler>"""
        err_msg = r".* has bad \$VAR references. Check for circular references or variables that are used in a \$VAR but not actually defined."
        with self.assertRaisesRegex(utils.CIMEError, err_msg):
            self.xml_to_tester(xml1 + xml2 + xml3)

    def test_override_with_machine_and_new_attributes(self):
        """Test that overrides with machine-specific settings with added attributes work correctly."""
        xml1 = """
<compiler COMPILER="{}">
  <SCC>icc</SCC>
  <MPICXX>mpicxx</MPICXX>
  <MPIFC>mpif90</MPIFC>
  <MPICC>mpicc</MPICC>
</compiler>""".format(
            self.test_compiler
        )
        xml2 = """
<compiler COMPILER="{}" MACH="{}">
  <MPICXX>mpifoo</MPICXX>
  <MPIFC MPILIB="{}">mpiffoo</MPIFC>
  <MPICC MPILIB="NOT_MY_MPI">mpifouc</MPICC>
</compiler>
""".format(
            self.test_compiler, self.test_machine, self.test_mpilib
        )

        tester = self.xml_to_tester(xml1 + xml2)

        tester.assert_variable_equals(
            "SCC",
            "icc",
            var={"COMPILER": self.test_compiler, "MPILIB": self.test_mpilib},
        )
        tester.assert_variable_equals(
            "MPICXX",
            "mpifoo",
            var={"COMPILER": self.test_compiler, "MPILIB": self.test_mpilib},
        )
        tester.assert_variable_equals(
            "MPIFC",
            "mpiffoo",
            var={"COMPILER": self.test_compiler, "MPILIB": self.test_mpilib},
        )
        tester.assert_variable_equals(
            "MPICC",
            "mpicc",
            var={"COMPILER": self.test_compiler, "MPILIB": self.test_mpilib},
        )

        tester = self.xml_to_tester(xml2 + xml1)

        tester.assert_variable_equals(
            "SCC",
            "icc",
            var={"COMPILER": self.test_compiler, "MPILIB": self.test_mpilib},
        )
        tester.assert_variable_equals(
            "MPICXX",
            "mpifoo",
            var={"COMPILER": self.test_compiler, "MPILIB": self.test_mpilib},
        )
        tester.assert_variable_equals(
            "MPIFC",
            "mpiffoo",
            var={"COMPILER": self.test_compiler, "MPILIB": self.test_mpilib},
        )
        tester.assert_variable_equals(
            "MPICC",
            "mpicc",
            var={"COMPILER": self.test_compiler, "MPILIB": self.test_mpilib},
        )

    def test_override_with_machine_and_same_attributes(self):
        """Test that machine-specific conditional overrides with the same attribute work correctly."""
        xml1 = """
<compiler COMPILER="{}">
  <MPIFC MPILIB="{}">mpifc</MPIFC>
</compiler>""".format(
            self.test_compiler, self.test_mpilib
        )
        xml2 = """
<compiler MACH="{}" COMPILER="{}">
  <MPIFC MPILIB="{}">mpif90</MPIFC>
</compiler>
""".format(
            self.test_machine, self.test_compiler, self.test_mpilib
        )

        tester = self.xml_to_tester(xml1 + xml2)

        tester.assert_variable_equals(
            "MPIFC",
            "mpif90",
            var={"COMPILER": self.test_compiler, "MPILIB": self.test_mpilib},
        )

        tester = self.xml_to_tester(xml2 + xml1)

        tester.assert_variable_equals(
            "MPIFC",
            "mpif90",
            var={"COMPILER": self.test_compiler, "MPILIB": self.test_mpilib},
        )

    def test_appends_not_overriden(self):
        """Test that machine-specific base value changes don't interfere with appends."""
        xml1 = """
<compiler COMPILER="{}">
 <FFLAGS>
   <base>-base1</base>
   <append DEBUG="FALSE">-debug1</append>
 </FFLAGS>
</compiler>""".format(
            self.test_compiler
        )

        xml2 = """
<compiler MACH="{}" COMPILER="{}">
 <FFLAGS>
   <base>-base2</base>
   <append DEBUG="TRUE">-debug2</append>
 </FFLAGS>
</compiler>""".format(
            self.test_machine, self.test_compiler
        )

        tester = self.xml_to_tester(xml1 + xml2)

        tester.assert_variable_equals(
            "FFLAGS", "-base2", var={"COMPILER": self.test_compiler}
        )
        tester.assert_variable_equals(
            "FFLAGS",
            "-base2 -debug2",
            var={"COMPILER": self.test_compiler, "DEBUG": "TRUE"},
        )
        tester.assert_variable_equals(
            "FFLAGS",
            "-base2 -debug1",
            var={"COMPILER": self.test_compiler, "DEBUG": "FALSE"},
        )

        tester = self.xml_to_tester(xml2 + xml1)

        tester.assert_variable_equals(
            "FFLAGS", "-base2", var={"COMPILER": self.test_compiler}
        )
        tester.assert_variable_equals(
            "FFLAGS",
            "-base2 -debug2",
            var={"COMPILER": self.test_compiler, "DEBUG": "TRUE"},
        )
        tester.assert_variable_equals(
            "FFLAGS",
            "-base2 -debug1",
            var={"COMPILER": self.test_compiler, "DEBUG": "FALSE"},
        )

    def test_multilevel_specificity(self):
        """Check that settings with multiple levels of machine-specificity can be resolved."""
        xml1 = """
<compiler>
 <MPIFC DEBUG="FALSE">mpifc</MPIFC>
</compiler>"""

        xml2 = """
<compiler OS="{}">
 <MPIFC MPILIB="{}">mpif03</MPIFC>
</compiler>""".format(
            self.test_os, self.test_mpilib
        )

        xml3 = """
<compiler MACH="{}">
 <MPIFC DEBUG="TRUE">mpif90</MPIFC>
</compiler>""".format(
            self.test_machine
        )

        # To verify order-independence, test every possible ordering of blocks.
        testers = []
        testers.append(self.xml_to_tester(xml1 + xml2 + xml3))
        testers.append(self.xml_to_tester(xml1 + xml3 + xml2))
        testers.append(self.xml_to_tester(xml2 + xml1 + xml3))
        testers.append(self.xml_to_tester(xml2 + xml3 + xml1))
        testers.append(self.xml_to_tester(xml3 + xml1 + xml2))
        testers.append(self.xml_to_tester(xml3 + xml2 + xml1))

        for tester in testers:
            tester.assert_variable_equals(
                "MPIFC",
                "mpif90",
                var={
                    "COMPILER": self.test_compiler,
                    "MPILIB": self.test_mpilib,
                    "DEBUG": "TRUE",
                },
            )
            tester.assert_variable_equals(
                "MPIFC",
                "mpif03",
                var={
                    "COMPILER": self.test_compiler,
                    "MPILIB": self.test_mpilib,
                    "DEBUG": "FALSE",
                },
            )
            tester.assert_variable_equals(
                "MPIFC",
                "mpifc",
                var={
                    "COMPILER": self.test_compiler,
                    "MPILIB": "NON_MATCHING_MPI",
                    "DEBUG": "FALSE",
                },
            )

    def test_remove_dependency_issues(self):
        """Check that overridden settings don't cause inter-variable dependencies."""
        xml1 = """
<compiler>
 <MPIFC>${SFC}</MPIFC>
</compiler>"""

        xml2 = (
            """
<compiler MACH="{}">""".format(
                self.test_machine
            )
            + """
 <SFC>${MPIFC}</SFC>
 <MPIFC>mpif90</MPIFC>
</compiler>"""
        )

        tester = self.xml_to_tester(xml1 + xml2)
        tester.assert_variable_equals("SFC", "mpif90")
        tester.assert_variable_equals("MPIFC", "mpif90")

        tester = self.xml_to_tester(xml2 + xml1)
        tester.assert_variable_equals("SFC", "mpif90")
        tester.assert_variable_equals("MPIFC", "mpif90")
