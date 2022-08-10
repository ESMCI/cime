import io
import os
import tempfile
import signal
import shutil
import sys
import time
from collections.abc import Iterable

from CIME import utils
from CIME import test_status
from CIME.utils import expect

MACRO_PRESERVE_ENV = [
    "ADDR2LINE",
    "AR",
    "AS",
    "CC",
    "CC_FOR_BUILD",
    "CMAKE_ARGS",
    "CONDA_EXE",
    "CONDA_PYTHON_EXE",
    "CPP",
    "CXX",
    "CXXFILT",
    "CXX_FOR_BUILD",
    "ELFEDIT",
    "F77",
    "F90",
    "F95",
    "FC",
    "GCC",
    "GCC_AR",
    "GCC_NM",
    "GCC_RANLIB",
    "GFORTRAN",
    "GPROF",
    "GXX",
    "LD",
    "LD_GOLD",
    "NM",
    "OBJCOPY",
    "OBJDUMP",
    "PATH",
    "RANLIB",
    "READELF",
    "SIZE",
    "STRINGS",
    "STRIP",
]


def parse_test_status(line):
    status, test = line.split()[0:2]
    return test, status


def make_fake_teststatus(path, testname, status, phase):
    expect(phase in test_status.CORE_PHASES, "Bad phase '%s'" % phase)
    with test_status.TestStatus(test_dir=path, test_name=testname) as ts:
        for core_phase in test_status.CORE_PHASES:
            if core_phase == phase:
                ts.set_status(
                    core_phase,
                    status,
                    comments=("time=42" if phase == test_status.RUN_PHASE else ""),
                )
                break
            else:
                ts.set_status(
                    core_phase,
                    test_status.TEST_PASS_STATUS,
                    comments=("time=42" if phase == test_status.RUN_PHASE else ""),
                )


class MockMachines(object):
    """A mock version of the Machines object to simplify testing."""

    def __init__(self, name, os_):
        """Store the name."""
        self.name = name
        self.os = os_

    def get_machine_name(self):
        """Return the name we were given."""
        return self.name

    def get_value(self, var_name):
        """Allow the operating system to be queried."""
        assert var_name == "OS", (
            "Build asked for a value not " "implemented in the testing infrastructure."
        )
        return self.os

    def is_valid_compiler(self, _):  # pylint:disable=no-self-use
        """Assume all compilers are valid."""
        return True

    def is_valid_MPIlib(self, _):
        """Assume all MPILIB settings are valid."""
        return True

    # pragma pylint: disable=unused-argument
    def get_default_MPIlib(self, attributes=None):
        return "mpich2"

    def get_default_compiler(self):
        return "intel"


class MakefileTester(object):

    """Helper class for checking Makefile output.

    Public methods:
    __init__
    query_var
    assert_variable_equals
    assert_variable_matches
    """

    # Note that the following is a Makefile and the echo line must begin with a tab
    _makefile_template = """
include Macros
query:
\techo '$({})' > query.out
"""

    def __init__(self, parent, make_string):
        """Constructor for Makefile test helper class.

        Arguments:
        parent - The TestCase object that is using this item.
        make_string - Makefile contents to test.
        """
        self.parent = parent
        self.make_string = make_string

    def query_var(self, var_name, env, var):
        """Request the value of a variable in the Makefile, as a string.

        Arguments:
        var_name - Name of the variable to query.
        env - A dict containing extra environment variables to set when calling
              make.
        var - A dict containing extra make variables to set when calling make.
              (The distinction between env and var actually matters only for
               CMake, though.)
        """
        if env is None:
            env = dict()
        if var is None:
            var = dict()

        # Write the Makefile strings to temporary files.
        temp_dir = tempfile.mkdtemp()
        macros_file_name = os.path.join(temp_dir, "Macros")
        makefile_name = os.path.join(temp_dir, "Makefile")
        output_name = os.path.join(temp_dir, "query.out")

        with open(macros_file_name, "w") as macros_file:
            macros_file.write(self.make_string)
        with open(makefile_name, "w") as makefile:
            makefile.write(self._makefile_template.format(var_name))

        # environment = os.environ.copy()
        environment = dict(PATH=os.environ["PATH"])
        environment.update(env)
        environment.update(var)
        for x in MACRO_PRESERVE_ENV:
            if x in os.environ:
                environment[x] = os.environ[x]
        gmake_exe = self.parent.MACHINE.get_value("GMAKE")
        if gmake_exe is None:
            gmake_exe = "gmake"
        self.parent.run_cmd_assert_result(
            "%s query --directory=%s 2>&1" % (gmake_exe, temp_dir), env=environment
        )

        with open(output_name, "r") as output:
            query_result = output.read().strip()

        # Clean up the Makefiles.
        shutil.rmtree(temp_dir)

        return query_result

    def assert_variable_equals(self, var_name, value, env=None, var=None):
        """Assert that a variable in the Makefile has a given value.

        Arguments:
        var_name - Name of variable to check.
        value - The string that the variable value should be equal to.
        env - Optional. Dict of environment variables to set when calling make.
        var - Optional. Dict of make variables to set when calling make.
        """
        self.parent.assertEqual(self.query_var(var_name, env, var), value)

    def assert_variable_matches(self, var_name, regex, env=None, var=None):
        """Assert that a variable in the Makefile matches a regex.

        Arguments:
        var_name - Name of variable to check.
        regex - The regex to match.
        env - Optional. Dict of environment variables to set when calling make.
        var - Optional. Dict of make variables to set when calling make.
        """
        self.parent.assertRegexpMatches(self.query_var(var_name, env, var), regex)


class CMakeTester(object):

    """Helper class for checking CMake output.

    Public methods:
    __init__
    query_var
    assert_variable_equals
    assert_variable_matches
    """

    _cmakelists_template = """
include(./Macros.cmake)
file(WRITE query.out "${{{}}}")
"""

    def __init__(self, parent, cmake_string):
        """Constructor for CMake test helper class.

        Arguments:
        parent - The TestCase object that is using this item.
        cmake_string - CMake contents to test.
        """
        self.parent = parent
        self.cmake_string = cmake_string

    def query_var(self, var_name, env, var):
        """Request the value of a variable in Macros.cmake, as a string.

        Arguments:
        var_name - Name of the variable to query.
        env - A dict containing extra environment variables to set when calling
              cmake.
        var - A dict containing extra CMake variables to set when calling cmake.
        """
        if env is None:
            env = dict()
        if var is None:
            var = dict()

        # Write the CMake strings to temporary files.
        temp_dir = tempfile.mkdtemp()
        macros_file_name = os.path.join(temp_dir, "Macros.cmake")
        cmakelists_name = os.path.join(temp_dir, "CMakeLists.txt")
        output_name = os.path.join(temp_dir, "query.out")

        with open(macros_file_name, "w") as macros_file:
            for key in var:
                macros_file.write("set({} {})\n".format(key, var[key]))
            macros_file.write(self.cmake_string)
        with open(cmakelists_name, "w") as cmakelists:
            cmakelists.write(self._cmakelists_template.format(var_name))

        # environment = os.environ.copy()
        environment = dict(PATH=os.environ["PATH"])
        environment.update(env)
        for x in MACRO_PRESERVE_ENV:
            if x in os.environ:
                environment[x] = os.environ[x]
        os_ = self.parent.MACHINE.get_value("OS")
        # cmake will not work on cray systems without this flag
        if os_ == "CNL":
            cmake_args = "-DCMAKE_SYSTEM_NAME=Catamount"
        else:
            cmake_args = ""

        self.parent.run_cmd_assert_result(
            "cmake %s . 2>&1" % cmake_args, from_dir=temp_dir, env=environment
        )

        with open(output_name, "r") as output:
            query_result = output.read().strip()

        # Clean up the CMake files.
        shutil.rmtree(temp_dir)

        return query_result

    def assert_variable_equals(self, var_name, value, env=None, var=None):
        """Assert that a variable in the CMakeLists has a given value.

        Arguments:
        var_name - Name of variable to check.
        value - The string that the variable value should be equal to.
        env - Optional. Dict of environment variables to set when calling cmake.
        var - Optional. Dict of CMake variables to set when calling cmake.
        """
        self.parent.assertEqual(self.query_var(var_name, env, var), value)

    def assert_variable_matches(self, var_name, regex, env=None, var=None):
        """Assert that a variable in the CMkeLists matches a regex.

        Arguments:
        var_name - Name of variable to check.
        regex - The regex to match.
        env - Optional. Dict of environment variables to set when calling cmake.
        var - Optional. Dict of CMake variables to set when calling cmake.
        """
        self.parent.assertRegexpMatches(self.query_var(var_name, env, var), regex)


# TODO after dropping python 2.7 replace with tempfile.TemporaryDirectory
class TemporaryDirectory(object):
    def __init__(self):
        self._tempdir = None

    def __enter__(self):
        self._tempdir = tempfile.mkdtemp()
        return self._tempdir

    def __exit__(self, *args, **kwargs):
        if os.path.exists(self._tempdir):
            shutil.rmtree(self._tempdir)


# TODO replace with actual mock once 2.7 is dropped
class Mocker:
    def __init__(self, ret=None, cmd=None, return_value=None, side_effect=None):
        self._orig = []
        self._ret = ret or return_value
        self._cmd = cmd
        self._calls = []

        if isinstance(side_effect, (list, tuple)):
            self._side_effect = iter(side_effect)
        else:
            self._side_effect = side_effect

        self._method_calls = {}

    @property
    def calls(self):
        return self._calls

    @property
    def method_calls(self):
        return dict((x, y.calls) for x, y in self._method_calls.items())

    @property
    def ret(self):
        return self._ret

    @ret.setter
    def ret(self, value):
        self._ret = value

    def assert_called(self):
        assert len(self.calls) > 0

    def assert_called_with(self, i=None, args=None, kwargs=None):
        if i is None:
            i = 0

        call = self.calls[i]

        if args is not None:
            _call_args = set(call["args"])
            _exp_args = set(args)
            assert _exp_args <= _call_args, "Got {} missing {}".format(
                _call_args, _exp_args - _call_args
            )

        if kwargs is not None:
            call_kwargs = call["kwargs"]

            for x, y in kwargs.items():
                assert call_kwargs[x] == y, "Missing {}".format(x)

    def __getattr__(self, name):
        if name in self._method_calls:
            new_method = self._method_calls[name]
        else:
            new_method = Mocker(self, cmd=name)
            self._method_calls[name] = new_method

        return new_method

    def __call__(self, *args, **kwargs):
        self._calls.append({"args": args, "kwargs": kwargs})

        if self._side_effect is not None and isinstance(self._side_effect, Iterable):
            rv = next(self._side_effect)
        else:
            rv = self._ret

        return rv

    def __del__(self):
        self.revert_mocks()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.revert_mocks()

    def revert_mocks(self):
        for m, module, method in self._orig:
            if isinstance(module, str):
                setattr(sys.modules[module], method, m)
            else:
                setattr(module, method, m)

    def patch(
        self, module, method=None, ret=None, is_property=False, update_value_only=False
    ):
        rv = None
        if isinstance(module, str):
            x = module.split(".")
            main = ".".join(x[:-1])
            if not update_value_only:
                self._orig.append((getattr(sys.modules[main], x[-1]), main, x[-1]))
            if is_property:
                setattr(sys.modules[main], x[-1], ret)
            else:
                rv = Mocker(ret, cmd=x[-1])
                setattr(sys.modules[main], x[-1], rv)
        elif method != None:
            if not update_value_only:
                self._orig.append((getattr(module, method), module, method))
            rv = Mocker(ret)
            setattr(module, method, rv)
        else:
            raise Exception("Could not patch")

        return rv
