#!/usr/bin/env python3
import os, sys

CESM_ROOT = os.getenv("CESM_ROOT")
if not CESM_ROOT:
    raise SystemExit("ERROR: CESM_ROOT must be defined in environment")

_LIBDIR = os.path.join(CESM_ROOT,"cime","scripts","Tools")
sys.path.append(_LIBDIR)
_LIBDIR = os.path.join(CESM_ROOT,"cime","scripts","lib")
sys.path.append(_LIBDIR)


import argparse, subprocess
from string import Template
from CIME.utils import run_cmd, expect
from CIME.case import Case

def parse_command_line(args, description):
    parser = argparse.ArgumentParser(description=description,
                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--db-nodes", default=1,
            help="Number of nodes for the SmartSim database, default=1")
    parser.add_argument("--ngpus-per-node", default=0,
            help="Number of gpus per SmartSim database node, default=0")
    parser.add_argument("--walltime", default="00:30:00",
            help="Total walltime for submitted job, default=00:30:00")
    parser.add_argument("--member-nodes", default=1,
            help="Number of nodes per ensemble member, default=1")
    parser.add_argument("--account", default="P93300606",
            help="Account ID")
    parser.add_argument("--db-port", default=6780,
            help="db port, default=6780")
    parser.add_argument("--caseroots" , default=[os.getcwd()],nargs="*",
            help="Case directory to reference.\n"
            "Default is current directory.")

    args = parser.parse_args(args[1:])
    ngpus = ""
    if int(args.ngpus_per_node) > 0:
        ngpus = ":ngpus="+args.ngpus_per_node

    return {"db_nodes":args.db_nodes,
        "caseroots" : ' '.join('"%s"' % x for x in args.caseroots),
        "ngpus": ngpus,
        "walltime": args.walltime,
        "account" : args.account,
        "db_port": args.db_port,
        "cesmroot": CESM_ROOT,
        "python_sys_path": sys.path}, args.caseroots

def create_submit_files(templatevars):
    template_files = ["resv_job.template", "launch_database_cluster.template"]
    rootdir = os.path.dirname(os.path.realpath(__file__))
    for template in template_files:
        with open(os.path.join(rootdir,template)) as f:
            src = Template(f.read())
            result = src.safe_substitute(templatevars)
            result_file = template.replace("template","sh")
        with open(result_file, "w") as f:
            f.write(result)

def check_cases(caseroots, db_nodes):
    """
    Assume all caseroots use the same number of nodes
    """
    prevcasepes = -1
    for caseroot in caseroots:
        with Case(caseroot, read_only=False) as case:
            expect(case.get_value("BUILD_COMPLETE"),"ERROR: case build not complete for {}".format(caseroot))
            casepes = case.get_value("TOTALPES")
            if prevcasepes > 0:
                expect(prevcasepes == casepes, "Case {} pe layout mismatch".format(caseroot))
            else:
                prevcasepes = casepes
                member_nodes = case.num_nodes
                case.set_value("CREATE_SMARTSIM_CLUSTER", db_nodes > 1)

    return member_nodes

def _main_func(desc):
    templatevars, caseroots = parse_command_line(sys.argv, desc)
    templatevars["member_nodes"] = check_cases(caseroots, int(templatevars["db_nodes"]))
    templatevars["ensemble_size"] = len(caseroots)
    templatevars["client_nodes"] = int(templatevars["member_nodes"])*len(caseroots)
    create_submit_files(templatevars)
    run_cmd("qsub resv_job.sh", verbose=True)




if __name__ == "__main__":
    _main_func(__doc__)
