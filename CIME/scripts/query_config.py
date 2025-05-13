#!/usr/bin/env python3
"""
Displays information about available compsets, component settings, grids and/or
machines. Typically run with one of the arguments --compsets, --settings,
--grids or --machines; if you specify more than one of these arguments,
information will be listed for each.
"""

import os
import sys
import logging
import argparse

from CIME.Tools.standard_script_setup import *
from CIME import utils
from CIME.XML.files import Files
from CIME.XML.component import Component
from CIME.XML.compsets import Compsets
from CIME.XML.grids import Grids
from CIME.XML.machines import Machines
from CIME.config import Config

logger = logging.getLogger(__name__)

customize_path = os.path.join(utils.get_src_root(), "cime_config", "customize")

config = Config.load(customize_path)


def _main_func(description=__doc__):
    kwargs = parse_command_line(description)

    if kwargs["grids"]:
        query_grids(**kwargs)

    if kwargs["compsets"] is not None:
        query_compsets(**kwargs)

    if kwargs["components"] is not None:
        query_component_settings(**kwargs)

    if kwargs["machines"] is not None:
        query_machines(**kwargs)


def parse_command_line(description):
    files = {x: Files(x) for x in list(config.driver_choices)}

    compset_active_components = get_compset_active_components(files)
    compset_active_components.extend(["all"])

    components = get_components(files)
    components.extend(["all"])

    default_driver = config.driver_default
    config_file = files[default_driver].get_value("MACHINES_SPEC_FILE")
    utils.expect(
        os.path.isfile(config_file),
        "Cannot find config_file {} on disk".format(config_file),
    )
    machines = Machines(config_file, machine="Query")
    machine_names = ["all", "current"]
    machine_names.extend(machines.list_available_machines())

    parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    config_group = parser.add_argument_group("Config options")

    config_group.add_argument(
        "--compsets",
        nargs="?",
        const="all",
        choices=sorted(set(compset_active_components)),
        help="Query compsets for active component. If no value is passed, compsets for all active components will be printed.",
    )

    config_group.add_argument(
        "--components",
        nargs="?",
        const="all",
        choices=sorted(set(components)),
        help="Query settings for component. If not value is passed, settings for all components will be printed.",
    )

    config_group.add_argument(
        "--grids", action="store_true", help="Query grids for model."
    )

    config_group.add_argument(
        "--machines",
        nargs="?",
        const="all",
        choices=machine_names,
        help="Query machines for model. If not value is passed, all machines will be printed.",
    )

    output_group = parser.add_argument_group("Output options")

    output_group.add_argument(
        "--long", action="store_true", help="Print extended output for queries."
    )

    output_group.add_argument("--xml", action="store_true", help="Print output in xml.")

    filter_group = parser.add_argument_group("Filter options")

    default_driver = config.driver_default

    filter_group.add_argument(
        "--driver",
        choices=config.driver_choices,
        default=default_driver,
        help=f"Filter by driver, defaults to {default_driver!r}.",
    )

    filter_group.add_argument(
        "--comp_interface",
        choices=config.driver_choices,
        default="mct",
        action=utils.deprecate_action(", use --driver argument"),
        help="DEPRECATED: Use --driver argument",
    )

    utils.setup_standard_logging_options(parser)

    kwargs = vars(parser.parse_args())

    utils.configure_logging(**kwargs)

    # make sure at least one argument has been passed
    if not any([kwargs[x] for x in ["grids", "compsets", "components", "machines"]]):
        parser.print_help(sys.stderr)

    kwargs["files"] = files[kwargs["driver"]]

    return kwargs


def get_compset_active_components(files):
    values = []

    for file in files.values():
        active_components = file.get_components("COMPSETS_SPEC_FILE")

        values.extend([x for x in active_components if x is not None])

    return values


def get_components(files):
    values = []

    for file in files.values():
        classes = get_component_classes(file)

        for c in classes:
            components = file.get_components(f"COMP_ROOT_DIR_{c}")

            values.extend([x for x in components if x is not None])

    return values


def get_component_classes(files):
    infile = files.get_value("CONFIG_CPL_FILE")

    config_drv = Component(infile, "CPL")

    return config_drv.get_valid_model_components()


def query_grids(files, long, xml, **_):
    config_file = files.get_value("GRIDS_SPEC_FILE")

    utils.expect(
        os.path.isfile(config_file),
        "Cannot find config_file {} on disk".format(config_file),
    )

    grids = Grids(config_file)

    if xml:
        print("{}".format(grids.get_raw_record().decode("UTF-8")))
    else:
        grids.print_values(long=long)


def query_compsets(files, compsets, **kwargs):
    if compsets == "all":
        active_components = files.get_components("COMPSETS_SPEC_FILE")

        for component in active_components:
            # the all_components flag will only print available components
            print_compset(component, files, all_components=True, **kwargs)
    else:
        print_compset(compsets, files, **kwargs)


def print_compset(name, files, xml=False, all_components=False, **_):
    """
    print compsets associated with the component name, but if all_components is true only
    print the details if the associated component is available
    """

    # Determine the config_file for the target component
    config_file = files.get_value("COMPSETS_SPEC_FILE", attribute={"component": name})
    # only error out if we aren't printing all otherwise exit quitely
    if not all_components:
        utils.expect(
            (config_file),
            "Cannot find any config_component.xml file for {}".format(name),
        )

        # Check that file exists on disk
        utils.expect(
            os.path.isfile(config_file),
            "Cannot find config_file {} on disk".format(config_file),
        )
    elif config_file is None or not os.path.isfile(config_file):
        return

    if config.test_mode not in ("e3sm", "cesm") and name == "drv":
        return

    print("\nActive component: {}".format(name))
    # Now parse the compsets file and write out the compset alias and longname as well as the help text
    # determine component xml content
    compsets = Compsets(config_file)
    # print compsets associated with component without help text
    if xml:
        print("{}".format(compsets.get_raw_record().decode("UTF-8")))
    else:
        compsets.print_values(arg_help=False)


def query_component_settings(components, files, **kwargs):
    classes = get_component_classes(files)

    if components == "all":
        # Loop through the elements for each component class (in config_files.xml)
        for comp in classes:
            string = "CONFIG_{}_FILE".format(comp)

            # determine all components in string
            components = files.get_components(string)

            for item in components:
                _query_component_settings(item, files, all_components=True, **kwargs)
    else:
        _query_component_settings(components, files, **kwargs)


def _query_component_settings(component, files, xml=False, all_components=False, **_):
    # Determine the valid component classes (e.g. atm) for the driver/cpl
    # These are then stored in comps_array
    classes = get_component_classes(files)

    # Loop through the elements for each component class (in config_files.xml)
    # and see if there is a match for the the target component in the component attribute
    match_found = False
    valid_components = []
    config_exists = False
    for comp in classes:
        string = "CONFIG_{}_FILE".format(comp)
        config_file = None
        # determine all components in string
        root_dir_node_name = "COMP_ROOT_DIR_{}".format(comp)
        _components = files.get_components(root_dir_node_name)
        if _components is None:
            _components = files.get_components(string)
        for item in _components:
            valid_components.append(item)
        logger.debug("{}: valid_components {}".format(comp, valid_components))
        # determine if config_file is on disk
        if component is None:
            config_file = files.get_value(string)
        elif component in valid_components:
            config_file = files.get_value(string, attribute={"component": component})
            logger.debug("query {}".format(config_file))
        if config_file is not None:
            match_found = True
            config_exists = os.path.isfile(config_file)
            break

    if not all_components and not config_exists:
        utils.expect(
            config_exists, "Cannot find config_file {} on disk".format(config_file)
        )
    elif all_components and not config_exists:
        print("WARNING: Couldn't find config_file {} on disk".format(config_file))
        return
    # If name is not a valid argument - exit with error
    utils.expect(
        match_found,
        "Invalid input argument {}, valid input arguments are {}".format(
            component, valid_components
        ),
    )

    # Check that file exists on disk, if not exit with error
    utils.expect(
        (config_file),
        "Cannot find any config_component.xml file for {}".format(component),
    )

    # determine component xml content
    component = Component(config_file, "CPL")
    if xml:
        print("{}".format(component.get_raw_record().decode("UTF-8")))
    else:
        component.print_values()


def query_machines(files, machines, xml, **_):
    config_file = files.get_value("MACHINES_SPEC_FILE")
    utils.expect(
        os.path.isfile(config_file),
        "Cannot find config_file {} on disk".format(config_file),
    )
    # Provide a special machine name indicating no need for a machine name
    xml_machines = Machines(config_file, machine="Query")
    if xml:
        if machines == "all":
            print("{}".format(machines.get_raw_record().decode("UTF-8")))
        else:
            xml_machines.set_machine(machines)
            print(
                "{}".format(
                    xml_machines.get_raw_record(root=machines.machine_node).decode(
                        "UTF-8"
                    )
                )
            )
    else:
        print_machine_values(xml_machines, machines)


def print_machine_values(
    machine, machine_name="all"
):  # pylint: disable=arguments-differ
    # set flag to look for single machine
    if "all" not in machine_name:
        single_machine = True
        if machine_name == "current":
            machine_name = machine.probe_machine_name(warn=False)
    else:
        single_machine = False

    # if we can't find the specified machine
    if single_machine and machine_name is None:
        files = Files()
        config_file = files.get_value("MACHINES_SPEC_FILE")
        print("Machine is not listed in config file: {}".format(config_file))
    else:  # write out machines
        if single_machine:
            machine_names = [machine_name]
        else:
            machine_names = machine.list_available_machines()
        print("Machine(s)\n")
        for name in machine_names:
            machine.set_machine(name)
            desc = machine.text(machine.get_child("DESC"))
            os_ = machine.text(machine.get_child("OS"))
            compilers = machine.text(machine.get_child("COMPILERS"))
            mpilibnodes = machine.get_children("MPILIBS", root=machine.machine_node)
            mpilibs = []
            for node in mpilibnodes:
                mpilibs.extend(machine.text(node).split(","))
            # This does not include the possible depedancy of mpilib on compiler
            # it simply provides a list of mpilibs available on the machine
            mpilibs = list(set(mpilibs))
            max_tasks_per_node = machine.text(machine.get_child("MAX_TASKS_PER_NODE"))
            mpitasks_node = machine.get_optional_child(
                "MAX_MPITASKS_PER_NODE", root=machine.machine_node
            )
            max_mpitasks_per_node = (
                machine.text(mpitasks_node) if mpitasks_node else max_tasks_per_node
            )
            max_gpus_node = machine.get_optional_child(
                "MAX_GPUS_PER_NODE", root=machine.machine_node
            )
            max_gpus_per_node = machine.text(max_gpus_node) if max_gpus_node else 0

            current_machine = machine.probe_machine_name(warn=False)
            name += " (current)" if current_machine and current_machine in name else ""
            print("  {} : {} ".format(name, desc))
            print("      os             ", os_)
            print("      compilers      ", compilers)
            print("      mpilibs        ", mpilibs)
            if max_mpitasks_per_node is not None:
                print("      pes/node       ", max_mpitasks_per_node)
            if max_tasks_per_node is not None:
                print("      max_tasks/node ", max_tasks_per_node)
            if max_gpus_per_node is not None:
                print("      max_gpus/node ", max_gpus_per_node)
            print("")


if __name__ == "__main__":
    _main_func(__doc__)
