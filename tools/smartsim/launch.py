#!/usr/bin/env python3
import os, sys

CESM_ROOT = os.getenv("CESM_ROOT")

_LIBDIR = os.path.join(CESM_ROOT,"cime","scripts","Tools")
if not os.path.isdir(_LIBDIR):
    raise SystemExit("ERROR: CESM_ROOT must be defined in environment {}".format(CESM_ROOT))
sys.path.append(_LIBDIR)
_LIBDIR = os.path.join(CESM_ROOT,"cime","scripts","lib")
if not os.path.isdir(_LIBDIR):
    raise SystemExit("ERROR: CESM_ROOT must be defined in environment")
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
    parser.add_argument("--logroot", default="/glade/scratch/{}".format(os.environ["USER"]),
                        help="Root directory under which SmartSimdb log files will be written")
    parser.add_argument("--dryrun", action="store_true",
                        help="Create job scripts, but do not submit")


    args = parser.parse_args(args[1:])
    ngpus = ""
    if int(args.ngpus_per_node) > 0:
        ngpus = ":ngpus="+args.ngpus_per_node

    expect(int(args.db_nodes) != 2, "db-nodes size of 2 not allowed, decrease to 1 or increase to 3 or more")
        

    return {"db_nodes":args.db_nodes,
	"caseroots" : ' '.join('"%s"' % x for x in args.caseroots),
	"ngpus": ngpus,
	"walltime": args.walltime,
	"account" : args.account,
	"db_port": args.db_port,
	"cesmroot": CESM_ROOT,
        "logroot" : args.logroot,
	"python_sys_path": sys.path}, args.caseroots, args.dryrun

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
    templatevars, caseroots, dryrun = parse_command_line(sys.argv, desc)
    templatevars["member_nodes"] = check_cases(caseroots, int(templatevars["db_nodes"]))
    templatevars["ensemble_size"] = len(caseroots)
    templatevars["client_nodes"] = int(templatevars["member_nodes"])*len(caseroots)
    print("Creating submit files")
    create_submit_files(templatevars)
    host = os.environ.get("NCAR_HOST")
    if host == "cheyenne":
        queue_name = "regular"
        gpu_flag = ""
    else:
        queue_name = "casper"
        gpu_flag =  "-l gpu_type=vt100"

    if not dryrun:
        print("Submitting job")
        _, o, e = run_cmd("qsub -q {} {} resv_job.sh ".format(queue_name, gpu_flag), verbose=True)
        if e:
            print("ERROR: {}".format(e))
        if o:
            print("{}".format(o))

if __name__ == "__main__":
    _main_func(__doc__)
