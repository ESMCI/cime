#!/usr/bin/env python3

"""This script writes CIME build information to a directory.

The pieces of information that will be written include:

1. Machine-specific build settings (i.e. the "Macros" file).
2. File-specific build settings (i.e. "Depends" files).
3. Environment variable loads (i.e. the env_mach_specific files).

The .env_mach_specific.sh and .env_mach_specific.csh files are specific to a
given compiler, MPI library, and DEBUG setting. By default, these will be the
machine's default compiler, the machine's default MPI library, and FALSE,
respectively. These can be changed by setting the environment variables
COMPILER, MPILIB, and DEBUG, respectively.
"""

from CIME.XML.standard_module_setup import *
from CIME.utils import expect, safe_copy, get_model, get_src_root, stringify_bool
from CIME.XML.compilers import Compilers
from CIME.XML.env_mach_specific import EnvMachSpecific
from CIME.XML.files import Files
from CIME.build import CmakeTmpBuildDir

import shutil, glob

logger = logging.getLogger(__name__)


def configure(
    machobj,
    output_dir,
    macros_format,
    compiler,
    mpilib,
    debug,
    comp_interface,
    sysos,
    unit_testing=False,
    noenv=False,
    threaded=False,
    extra_machines_dir=None,
):
    """Add Macros, Depends, and env_mach_specific files to a directory.

    Arguments:
    machobj - Machines argument for this machine.
    output_dir - Directory in which to place output.
    macros_format - Container containing the string 'Makefile' to produce
                    Makefile Macros output, and/or 'CMake' for CMake output.
    compiler - String containing the compiler vendor to configure for.
    mpilib - String containing the MPI implementation to configure for.
    debug - Boolean specifying whether debugging options are enabled.
    unit_testing - Boolean specifying whether we're running unit tests (as
                   opposed to a system run)
    extra_machines_dir - String giving path to an additional directory that will be
                         searched for a config_compilers.xml file.
    """
    # Macros generation.
    suffixes = {"Makefile": "make", "CMake": "cmake"}

    new_cmake_macros_dir = Files(comp_interface=comp_interface).get_value(
        "CMAKE_MACROS_DIR"
    )
    macro_maker = None
    for form in macros_format:

        if (
            new_cmake_macros_dir is not None
            and os.path.exists(new_cmake_macros_dir)
            and not "CIME_NO_CMAKE_MACRO" in os.environ
        ):

            if not os.path.isfile(os.path.join(output_dir, "Macros.cmake")):
                safe_copy(
                    os.path.join(new_cmake_macros_dir, "Macros.cmake"), output_dir
                )
            if not os.path.exists(os.path.join(output_dir, "cmake_macros")):
                shutil.copytree(
                    new_cmake_macros_dir, os.path.join(output_dir, "cmake_macros")
                )

            # Grab macros from extra machine dir if it was provided
            if extra_machines_dir:
                extra_cmake_macros = glob.glob("{}/cmake_macros/*.cmake".format(extra_machines_dir))
                for extra_cmake_macro in extra_cmake_macros:
                    safe_copy(extra_cmake_macro, new_cmake_macros_dir)

            if form == "Makefile":
                # Use the cmake macros to generate the make macros
                cmake_args = " -DOS={} -DMACH={} -DCOMPILER={} -DDEBUG={} -DMPILIB={} -Dcompile_threaded={} -DCASEROOT={}".format(
                    sysos,
                    machobj.get_machine_name(),
                    compiler,
                    stringify_bool(debug),
                    mpilib,
                    stringify_bool(threaded),
                    output_dir,
                )

                with CmakeTmpBuildDir(macroloc=output_dir) as cmaketmp:
                    output = cmaketmp.get_makefile_vars(cmake_args=cmake_args)

                with open(os.path.join(output_dir, "Macros.make"), "w") as fd:
                    fd.write(output)

        else:
            logger.warning("Using deprecated CIME makefile generators")
            if macro_maker is None:
                macro_maker = Compilers(
                    machobj,
                    compiler=compiler,
                    mpilib=mpilib,
                    extra_machines_dir=extra_machines_dir,
                )

            out_file_name = os.path.join(output_dir, "Macros." + suffixes[form])
            macro_maker.write_macros_file(
                macros_file=out_file_name, output_format=suffixes[form]
            )

    copy_depends_files(
        machobj.get_machine_name(), machobj.machines_dir, output_dir, compiler
    )
    generate_env_mach_specific(
        output_dir,
        machobj,
        compiler,
        mpilib,
        debug,
        comp_interface,
        sysos,
        unit_testing,
        threaded,
        noenv=noenv,
    )


def copy_depends_files(machine_name, machines_dir, output_dir, compiler):
    """
    Copy any system or compiler Depends files if they do not exist in the output directory
    If there is a match for Depends.machine_name.compiler copy that and ignore the others
    """
    # Note, the cmake build system does not stop if Depends.mach.compiler.cmake is found
    makefiles_done = False
    both = "{}.{}".format(machine_name, compiler)
    for suffix in [both, machine_name, compiler]:
        for extra_suffix in ["", ".cmake"]:
            if extra_suffix == "" and makefiles_done:
                continue

            basename = "Depends.{}{}".format(suffix, extra_suffix)
            dfile = os.path.join(machines_dir, basename)
            outputdfile = os.path.join(output_dir, basename)
            if os.path.isfile(dfile):
                if suffix == both and extra_suffix == "":
                    makefiles_done = True
                if not os.path.exists(outputdfile):
                    safe_copy(dfile, outputdfile)


class FakeCase(object):
    def __init__(self, compiler, mpilib, debug, comp_interface, threading=False):
        # PIO_VERSION is needed to parse config_machines.xml but isn't otherwise used
        # by FakeCase
        self._vals = {
            "COMPILER": compiler,
            "MPILIB": mpilib,
            "DEBUG": debug,
            "COMP_INTERFACE": comp_interface,
            "PIO_VERSION": 2,
            "SMP_PRESENT": threading,
            "MODEL": get_model(),
            "SRCROOT": get_src_root(),
        }

    def get_build_threaded(self):
        return self.get_value("SMP_PRESENT")

    def get_value(self, attrib):
        expect(
            attrib in self._vals,
            "FakeCase does not support getting value of '%s'" % attrib,
        )
        return self._vals[attrib]


def generate_env_mach_specific(
    output_dir,
    machobj,
    compiler,
    mpilib,
    debug,
    comp_interface,
    sysos,
    unit_testing,
    threaded,
    noenv=False,
):
    """
    env_mach_specific generation.
    """
    ems_path = os.path.join(output_dir, "env_mach_specific.xml")
    if os.path.exists(ems_path):
        logger.warning("{} already exists, delete to replace".format(ems_path))
        return

    ems_file = EnvMachSpecific(
        output_dir, unit_testing=unit_testing, standalone_configure=True
    )
    ems_file.populate(
        machobj,
        attributes={"mpilib": mpilib, "compiler": compiler, "threaded": threaded},
    )
    ems_file.write()

    if noenv:
        return

    fake_case = FakeCase(compiler, mpilib, debug, comp_interface)
    ems_file.load_env(fake_case)
    for shell in ("sh", "csh"):
        ems_file.make_env_mach_specific_file(shell, fake_case, output_dir=output_dir)
        shell_path = os.path.join(output_dir, ".env_mach_specific." + shell)
        with open(shell_path, "a") as shell_file:
            if shell == "sh":
                shell_file.write("\nexport COMPILER={}\n".format(compiler))
                shell_file.write("export MPILIB={}\n".format(mpilib))
                shell_file.write("export DEBUG={}\n".format(repr(debug).upper()))
                shell_file.write("export OS={}\n".format(sysos))
            else:
                shell_file.write("\nsetenv COMPILER {}\n".format(compiler))
                shell_file.write("setenv MPILIB {}\n".format(mpilib))
                shell_file.write("setenv DEBUG {}\n".format(repr(debug).upper()))
                shell_file.write("setenv OS {}\n".format(sysos))
