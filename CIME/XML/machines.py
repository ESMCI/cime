"""
Interface to the config_machines.xml file.  This class inherits from GenericXML.py
"""
from CIME.XML.standard_module_setup import *
from CIME.XML.generic_xml import GenericXML
from CIME.XML.files import Files
from CIME.utils import convert_to_unknown_type, get_cime_config

import socket
from pathlib import Path

logger = logging.getLogger(__name__)


class Machines(GenericXML):
    def __init__(
        self,
        infile=None,
        files=None,
        machine=None,
        extra_machines_dir=None,
        read_only=True,
    ):
        """
        initialize an object
        if a filename is provided it will be used,
        otherwise if a files object is provided it will be used
        otherwise create a files object from default values

        If extra_machines_dir is provided, it should be a string giving a path to an
        additional directory that will be searched for a config_machines.xml file; if
        found, the contents of this file will be appended to the standard
        config_machines.xml. An empty string is treated the same as None.

        The schema variable can be passed as a path to an xsd schema file or a dictionary of paths
        with version number as keys.
        """

        self.machine_node = None
        self.machine = None
        self.machines_dir = None
        self.custom_settings = {}
        self.extra_machines_dir = extra_machines_dir

        schema = None
        checked_files = []
        if files is None:
            files = Files()
        if infile is None:
            infile = files.get_value("MACHINES_SPEC_FILE")

        self.machines_dir = os.path.dirname(infile)
        if os.path.exists(infile):
            checked_files.append(infile)
        else:
            expect(False, f"file not found {infile}")

        schema = {
            "3.0": files.get_schema(
                "MACHINES_SPEC_FILE", attributes={"version": "3.0"}
            ),
            "2.0": files.get_schema(
                "MACHINES_SPEC_FILE", attributes={"version": "2.0"}
            ),
        }
        # Before v3 there was but one choice
        if not schema["3.0"]:
            schema = files.get_schema("MACHINES_SPEC_FILE")

        logger.debug("Verifying using schema {}".format(schema))

        GenericXML.__init__(self, infile, schema, read_only=read_only)

        # Append the contents of $HOME/.cime/config_machines.xml if it exists.
        #
        # Also append the contents of a config_machines.xml file in the directory given by
        # extra_machines_dir, if present.
        #
        # This could cause problems if node matches are repeated when only one is expected.
        local_infile = os.path.join(
            os.environ.get("HOME"), ".cime", "config_machines.xml"
        )
        logger.debug("Infile: {}".format(local_infile))

        if os.path.exists(local_infile):
            GenericXML.read(self, local_infile, schema)
            checked_files.append(local_infile)

        if extra_machines_dir:
            local_infile = os.path.join(extra_machines_dir, "config_machines.xml")
            logger.debug("Infile: {}".format(local_infile))
            if os.path.exists(local_infile):
                GenericXML.read(self, local_infile, schema)
                checked_files.append(local_infile)

        if machine is None:
            if "CIME_MACHINE" in os.environ:
                machine = os.environ["CIME_MACHINE"]
            else:
                cime_config = get_cime_config()
                if cime_config.has_option("main", "machine"):
                    machine = cime_config.get("main", "machine")
                if machine is None:
                    machine = self.probe_machine_name()

        expect(
            machine is not None,
            f"Could not initialize machine object from {', '.join(checked_files)}. This machine is not available for the target CIME_MODEL.",
        )
        self.set_machine(machine, schema=schema)

    def get_child(self, name=None, attributes=None, root=None, err_msg=None):
        if root is None:
            root = self.machine_node
        return super(Machines, self).get_child(name, attributes, root, err_msg)

    def get_machines_dir(self):
        """
        Return the directory of the machines file
        """
        return self.machines_dir

    def get_extra_machines_dir(self):
        return self.extra_machines_dir

    def get_machine_name(self):
        """
        Return the name of the machine
        """
        return self.machine

    def get_node_names(self):
        """
        Return the names of all the child nodes for the target machine
        """
        nodes = self.get_children(root=self.machine_node)
        node_names = []
        for node in nodes:
            node_names.append(self.name(node))
        return node_names

    def get_first_child_nodes(self, nodename):
        """
        Return the names of all the child nodes for the target machine
        """
        nodes = self.get_children(nodename, root=self.machine_node)
        return nodes

    def list_available_machines(self):
        """
        Return a list of machines defined for a given CIME_MODEL
        """
        machines = []
        nodes = self.get_children("machine")
        for node in nodes:
            mach = self.get(node, "MACH")
            machines.append(mach)
        if self.get_version() == 3.0:
            machdirs = [
                os.path.basename(f.path)
                for f in os.scandir(self.machines_dir)
                if f.is_dir()
            ]
            machdirs.remove("cmake_macros")
            machdirs.remove("userdefined_laptop_template")
            for mach in machdirs:
                if mach not in machines:
                    machines.append(mach)

        machines.sort()
        return machines

    def probe_machine_name(self, warn=True):
        """
        Find a matching regular expression for hostname
        in the NODENAME_REGEX field in the file.   First match wins.
        """

        names_not_found = []

        nametomatch = socket.getfqdn()

        machine = self._probe_machine_name_one_guess(nametomatch)

        if machine is None:
            names_not_found.append(nametomatch)

            nametomatch = socket.gethostname()
            machine = self._probe_machine_name_one_guess(nametomatch)

            if machine is None:
                names_not_found.append(nametomatch)

                names_not_found_quoted = ["'" + name + "'" for name in names_not_found]
                names_not_found_str = " or ".join(names_not_found_quoted)
                if warn:
                    logger.debug(
                        "Could not find machine match for {}".format(
                            names_not_found_str
                        )
                    )

        return machine

    def _probe_machine_name_one_guess(self, nametomatch):
        """
        Find a matching regular expression for nametomatch in the NODENAME_REGEX
        field in the file. First match wins. Returns None if no match is found.
        """
        if self.get_version() < 3:
            return self._probe_machine_name_one_guess_v2(nametomatch)
        else:
            return self._probe_machine_name_one_guess_v3(nametomatch)

    def _probe_machine_name_one_guess_v2(self, nametomatch):

        nodes = self.get_children("machine")
        machine = None
        for node in nodes:
            machtocheck = self.get(node, "MACH")
            logger.debug("machine is " + machtocheck)
            regex_str_node = self.get_optional_child("NODENAME_REGEX", root=node)
            regex_str = (
                machtocheck if regex_str_node is None else self.text(regex_str_node)
            )

            if regex_str is not None:
                logger.debug("machine regex string is " + regex_str)
                # an environment variable can be used
                if regex_str.startswith("$ENV"):
                    machine_value = self.get_resolved_value(
                        regex_str, allow_unresolved_envvars=True
                    )
                    if not machine_value.startswith("$ENV"):
                        try:
                            match, this_machine = machine_value.split(":")
                        except ValueError:
                            expect(
                                False,
                                "Bad formation of NODENAME_REGEX.  Expected envvar:value, found {}".format(
                                    regex_str
                                ),
                            )
                        if match == this_machine:
                            machine = machtocheck
                            break
                else:
                    regex = re.compile(regex_str)
                    if regex.match(nametomatch):
                        logger.debug(
                            "Found machine: {} matches {}".format(
                                machtocheck, nametomatch
                            )
                        )
                        machine = machtocheck
                        break

        return machine

    def _probe_machine_name_one_guess_v3(self, nametomatch):

        nodes = self.get_children("NODENAME_REGEX", root=self.root)

        children = [y for x in nodes for y in self.get_children(root=x)]

        machine = None
        for child in children:
            machtocheck = self.get(child, "MACH")
            regex_str = self.text(child)
            logger.debug(
                "machine is {} regex {}, nametomatch {}".format(
                    machtocheck, regex_str, nametomatch
                )
            )

            if regex_str is not None:
                # an environment variable can be used
                if regex_str.startswith("$ENV"):
                    machine_value = self.get_resolved_value(
                        regex_str, allow_unresolved_envvars=True
                    )
                    logger.debug("machine_value is {}".format(machine_value))
                    if not machine_value.startswith("$ENV"):
                        try:
                            match, this_machine = machine_value.split(":")
                        except ValueError:
                            expect(
                                False,
                                "Bad formation of NODENAME_REGEX.  Expected envvar:value, found {}".format(
                                    regex_str
                                ),
                            )
                        if match == this_machine:
                            machine = machtocheck
                            break
                else:
                    regex = re.compile(regex_str)
                    if regex.match(nametomatch):
                        logger.debug(
                            "Found machine: {} matches {}".format(
                                machtocheck, nametomatch
                            )
                        )
                        machine = machtocheck
                        break

        return machine

    def set_machine(self, machine, schema=None):
        """
        Sets the machine block in the Machines object

        >>> machobj = Machines(machine="melvin")
        >>> machobj.get_machine_name()
        'melvin'
        >>> machobj.set_machine("trump") # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        CIMEError: ERROR: No machine trump found
        """
        if machine == "Query":
            return machine
        elif self.get_version() == 3:
            machines_file = Path.home() / ".cime" / machine / "config_machines.xml"

            if machines_file.exists():
                GenericXML.read(
                    self,
                    machines_file,
                    schema=schema,
                )
            else:
                machines_file = (
                    Path(self.machines_dir) / machine / "config_machines.xml"
                )

                if machines_file.exists():
                    GenericXML.read(
                        self,
                        machines_file,
                        schema=schema,
                    )
        self.machine_node = super(Machines, self).get_child(
            "machine",
            {"MACH": machine},
            err_msg="No machine {} found".format(machine),
        )

        self.machine = machine
        return machine

    # pylint: disable=arguments-differ
    def get_value(self, name, attributes=None, resolved=True, subgroup=None):
        """
        Get Value of fields in the config_machines.xml file
        """
        if self.machine_node is None:
            logger.debug("Machine object has no machine defined")
            return None

        expect(subgroup is None, "This class does not support subgroups")
        value = None

        if name in self.custom_settings:
            return self.custom_settings[name]

        # COMPILER and MPILIB are special, if called without arguments they get the default value from the
        # COMPILERS and MPILIBS lists in the file.
        if name == "COMPILER":
            value = self.get_default_compiler()
        elif name == "MPILIB":
            value = self.get_default_MPIlib(attributes)
        else:
            node = self.get_optional_child(
                name, root=self.machine_node, attributes=attributes
            )
            if node is not None:
                value = self.text(node)

        if resolved:
            if value is not None:
                value = self.get_resolved_value(value)
            elif name in os.environ:
                value = os.environ[name]

            value = convert_to_unknown_type(value)

        return value

    def get_field_from_list(self, listname, reqval=None, attributes=None):
        """
        Some of the fields have lists of valid values in the xml, parse these
        lists and return the first value if reqval is not provided and reqval
        if it is a valid setting for the machine
        """
        expect(self.machine_node is not None, "Machine object has no machine defined")
        supported_values = self.get_value(listname, attributes=attributes)
        logger.debug(
            "supported values for {} on {} is {}".format(
                listname, self.machine, supported_values
            )
        )
        # if no match with attributes, try without
        if supported_values is None:
            supported_values = self.get_value(listname, attributes=None)

        expect(
            supported_values is not None,
            "No list found for " + listname + " on machine " + self.machine,
        )
        supported_values = supported_values.split(",")  # pylint: disable=no-member

        if reqval is None or reqval == "UNSET":
            return supported_values[0]

        for val in supported_values:
            if val == reqval:
                return reqval
        return None

    def get_default_compiler(self):
        """
        Get the compiler to use from the list of COMPILERS
        """
        cime_config = get_cime_config()
        if cime_config.has_option("main", "COMPILER"):
            value = cime_config.get("main", "COMPILER")
            expect(
                self.is_valid_compiler(value),
                "User-selected compiler {} is not supported on machine {}".format(
                    value, self.machine
                ),
            )
        else:
            value = self.get_field_from_list("COMPILERS")
        return value

    def get_default_MPIlib(self, attributes=None):
        """
        Get the MPILIB to use from the list of MPILIBS
        """
        return self.get_field_from_list("MPILIBS", attributes=attributes)

    def is_valid_compiler(self, compiler):
        """
        Check the compiler is valid for the current machine
        """
        return self.get_field_from_list("COMPILERS", reqval=compiler) is not None

    def is_valid_MPIlib(self, mpilib, attributes=None):
        """
        Check the MPILIB is valid for the current machine
        """
        return (
            mpilib == "mpi-serial"
            or self.get_field_from_list("MPILIBS", reqval=mpilib, attributes=attributes)
            is not None
        )

    def has_batch_system(self):
        """
        Return if this machine has a batch system
        """
        result = False
        batch_system = self.get_optional_child("BATCH_SYSTEM", root=self.machine_node)
        if batch_system is not None:
            result = (
                self.text(batch_system) is not None
                and self.text(batch_system) != "none"
            )
        logger.debug("Machine {} has batch: {}".format(self.machine, result))
        return result

    def get_suffix(self, suffix_type):
        node = self.get_optional_child("default_run_suffix")
        if node is not None:
            suffix_node = self.get_optional_child(suffix_type, root=node)
            if suffix_node is not None:
                return self.text(suffix_node)

        return None

    def set_value(self, vid, value, subgroup=None, ignore_type=True):
        # A temporary cache only
        self.custom_settings[vid] = value

    def print_values(self):
        # write out machines
        machines = self.get_children("machine")
        logger.info("Machines")
        for machine in machines:
            name = self.get(machine, "MACH")
            desc = self.get_child("DESC", root=machine)
            os_ = self.get_child("OS", root=machine)
            compilers = self.get_child("COMPILERS", root=machine)
            max_tasks_per_node = self.get_child("MAX_TASKS_PER_NODE", root=machine)
            max_mpitasks_per_node = self.get_child(
                "MAX_MPITASKS_PER_NODE", root=machine
            )
            max_gpus_per_node = self.get_child("MAX_GPUS_PER_NODE", root=machine)

            print("  {} : {} ".format(name, self.text(desc)))
            print("      os             ", self.text(os_))
            print("      compilers      ", self.text(compilers))
            if max_mpitasks_per_node is not None:
                print("      pes/node       ", self.text(max_mpitasks_per_node))
            if max_tasks_per_node is not None:
                print("      max_tasks/node ", self.text(max_tasks_per_node))
            if max_gpus_per_node is not None:
                print("      max_gpus/node ", self.text(max_gpus_per_node))

    def return_values(self):
        """return a dictionary of machine info
        This routine is used by external tools in https://github.com/NCAR/CESM_xml2html
        """
        machines = self.get_children("machine")
        mach_dict = dict()
        logger.debug("Machines return values")
        for machine in machines:
            name = self.get(machine, "MACH")
            desc = self.get_child("DESC", root=machine)
            mach_dict[(name, "description")] = self.text(desc)
            os_ = self.get_child("OS", root=machine)
            mach_dict[(name, "os")] = self.text(os_)
            compilers = self.get_child("COMPILERS", root=machine)
            mach_dict[(name, "compilers")] = self.text(compilers)
            max_tasks_per_node = self.get_child("MAX_TASKS_PER_NODE", root=machine)
            mach_dict[(name, "max_tasks_per_node")] = self.text(max_tasks_per_node)
            max_mpitasks_per_node = self.get_child(
                "MAX_MPITASKS_PER_NODE", root=machine
            )
            mach_dict[(name, "max_mpitasks_per_node")] = self.text(
                max_mpitasks_per_node
            )
            max_gpus_per_node = self.get_child("MAX_GPUS_PER_NODE", root=machine)
            mach_dict[(name, "max_gpus_per_node")] = self.text(max_gpus_per_node)

        return mach_dict
