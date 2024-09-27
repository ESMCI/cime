# These routines were moved from utils.py to avoid circular dependancies
import time, os, sys, logging
from CIME.utils import Timeout, CASE_SUCCESS, CASE_FAILURE

logger = logging.getLogger(__name__)


def append_status(msg, sfile, caseroot="."):
    """
    Append msg to sfile in caseroot
    """
    ctime = time.strftime("%Y-%m-%d %H:%M:%S: ")

    # Reduce empty lines in CaseStatus. It's a very concise file
    # and does not need extra newlines for readability
    line_ending = "\n"
    with open(os.path.join(caseroot, sfile), "a") as fd:
        fd.write(ctime + msg + line_ending)
        fd.write(" ---------------------------------------------------" + line_ending)


def append_testlog(msg, caseroot="."):
    """
    Add to TestStatus.log file
    """
    append_status(msg, "TestStatus.log", caseroot)


def append_case_status(phase, status, msg=None, caseroot=".", gitinterface=None):
    """
    Update CaseStatus file
    """
    msg = msg if msg else ""
    append_status(
        "{} {} {}".format(phase, status, msg),
        "CaseStatus",
        caseroot,
    )
    if gitinterface:
        filelist = gitinterface.git_operation(
            "ls-files", "--deleted", "--exclude-standard"
        )
        # First delete files that have been removed
        if filelist:
            for f in filelist.splitlines():
                logger.debug("removing file {}".format(f))
                gitinterface.git_operation("rm", f)
        filelist = gitinterface.git_operation(
            "ls-files", "--others", "--modified", "--exclude-standard"
        )
        # Files that should not be added should have been excluded by the .gitignore file
        if filelist:
            for f in filelist.splitlines():
                logger.debug("adding file {}".format(f))
                gitinterface.git_operation("add", f)
        msg = msg if msg else " no message provided"
        gitinterface.git_operation("commit", "-m", '"' + msg + '"')
        remote = gitinterface.git_operation("remote")
        if remote:
            with Timeout(30):
                gitinterface.git_operation("push", remote)


def run_and_log_case_status(
    func,
    phase,
    caseroot=".",
    custom_starting_msg_functor=None,
    custom_success_msg_functor=None,
    is_batch=False,
    gitinterface=None,
):
    starting_msg = None

    if custom_starting_msg_functor is not None:
        starting_msg = custom_starting_msg_functor()

    # Delay appending "starting" on "case.subsmit" phase when batch system is
    # present since we don't have the jobid yet
    if phase != "case.submit" or not is_batch:
        append_case_status(
            phase,
            "starting",
            msg=starting_msg,
            caseroot=caseroot,
            gitinterface=gitinterface,
        )
    rv = None
    try:
        rv = func()
    except BaseException:
        custom_success_msg = (
            custom_success_msg_functor(rv)
            if custom_success_msg_functor and rv is not None
            else None
        )
        if phase == "case.submit" and is_batch:
            append_case_status(
                phase,
                "starting",
                msg=custom_success_msg,
                caseroot=caseroot,
                gitinterface=gitinterface,
            )
        e = sys.exc_info()[1]
        append_case_status(
            phase,
            CASE_FAILURE,
            msg=("\n{}".format(e)),
            caseroot=caseroot,
            gitinterface=gitinterface,
        )
        raise
    else:
        custom_success_msg = (
            custom_success_msg_functor(rv) if custom_success_msg_functor else None
        )
        if phase == "case.submit" and is_batch:
            append_case_status(
                phase,
                "starting",
                msg=custom_success_msg,
                caseroot=caseroot,
                gitinterface=gitinterface,
            )
        append_case_status(
            phase,
            CASE_SUCCESS,
            msg=custom_success_msg,
            caseroot=caseroot,
            gitinterface=gitinterface,
        )

    return rv
