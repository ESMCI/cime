"""
Libraries for checking python code with pylint
"""

import os
import json

from CIME.XML.standard_module_setup import *

from CIME.utils import (
    run_cmd,
    run_cmd_no_fail,
    expect,
    get_cime_root,
    get_src_root,
    is_python_executable,
    get_cime_default_driver,
)

from multiprocessing.dummy import Pool as ThreadPool

# pylint: disable=import-error
from distutils.spawn import find_executable

logger = logging.getLogger(__name__)


###############################################################################
def _run_pylint(all_files, interactive):
    ###############################################################################
    pylint = find_executable("pylint")

    cmd_options = (
        " --disable=I,C,R,logging-not-lazy,wildcard-import,unused-wildcard-import"
    )
    cmd_options += (
        ",fixme,broad-except,bare-except,eval-used,exec-used,global-statement"
    )
    cmd_options += ",logging-format-interpolation,no-name-in-module,arguments-renamed"
    cmd_options += " -j 0 -f json"
    cimeroot = get_cime_root()
    srcroot = get_src_root()

    # if "scripts/Tools" in on_file:
    #     cmd_options +=",relative-import"

    # add init-hook option
    cmd_options += (
        ' --init-hook=\'import sys; sys.path.extend(("%s","%s","%s","%s"))\''
        % (
            os.path.join(cimeroot, "CIME"),
            os.path.join(cimeroot, "CIME", "Tools"),
            os.path.join(cimeroot, "scripts", "fortran_unit_testing", "python"),
            os.path.join(srcroot, "components", "cmeps", "cime_config", "runseq"),
        )
    )

    files = " ".join(all_files)
    cmd = "%s %s %s" % (pylint, cmd_options, files)
    logger.debug("pylint command is %s" % cmd)
    stat, out, err = run_cmd(cmd, verbose=False, from_dir=cimeroot)

    data = json.loads(out)

    result = {}

    for item in data:
        if item["type"] != "error":
            continue

        path = item["path"]
        message = item["message"]
        line = item["line"]

        if path in result:
            result[path].append(f"{message}:{line}")
        else:
            result[path] = [
                message,
            ]

    for k in result.keys():
        result[k] = "\n".join(set(result[k]))

    return result


###############################################################################
def _matches(file_path, file_ends):
    ###############################################################################
    for file_end in file_ends:
        if file_path.endswith(file_end):
            return True

    return False


###############################################################################
def _should_pylint_skip(filepath):
    ###############################################################################
    # TODO - get rid of this
    list_of_directories_to_ignore = (
        "xmlconvertors",
        "pointclm",
        "point_clm",
        "tools",
        "machines",
        "apidocs",
        "doc",
    )
    for dir_to_skip in list_of_directories_to_ignore:
        if dir_to_skip + "/" in filepath:
            return True
        # intended to be temporary, file needs update
        if filepath.endswith("archive_metadata") or filepath.endswith("pgn.py"):
            return True

    return False


###############################################################################
def get_all_checkable_files():
    ###############################################################################
    cimeroot = get_cime_root()
    all_git_files = run_cmd_no_fail(
        "git ls-files", from_dir=cimeroot, verbose=False
    ).splitlines()
    if get_cime_default_driver() == "nuopc":
        srcroot = get_src_root()
        nuopc_git_files = []
        try:
            nuopc_git_files = run_cmd_no_fail(
                "git ls-files",
                from_dir=os.path.join(srcroot, "components", "cmeps"),
                verbose=False,
            ).splitlines()
        except:
            logger.warning("No nuopc driver found in source")
        all_git_files.extend(
            [
                os.path.join(srcroot, "components", "cmeps", _file)
                for _file in nuopc_git_files
            ]
        )
    files_to_test = [
        item
        for item in all_git_files
        if (
            (item.endswith(".py") or is_python_executable(os.path.join(cimeroot, item)))
            and not _should_pylint_skip(item)
        )
    ]

    return files_to_test


###############################################################################
def check_code(files, num_procs=10, interactive=False):
    ###############################################################################
    """
    Check all python files in the given directory

    Returns True if all files had no problems
    """
    # Get list of files to check, we look to see if user-provided file argument
    # is a valid file, if not, we search the repo for a file with similar name.
    files_to_check = []
    if files:
        repo_files = get_all_checkable_files()
        for filearg in files:
            if os.path.exists(filearg):
                files_to_check.append(os.path.abspath(filearg))
            else:
                found = False
                for repo_file in repo_files:
                    if repo_file.endswith(filearg):
                        found = True
                        files_to_check.append(repo_file)  # could have multiple matches

                if not found:
                    logger.warning(
                        "Could not find file matching argument '%s'" % filearg
                    )
    else:
        # Check every python file
        files_to_check = get_all_checkable_files()

    expect(len(files_to_check) > 0, "No matching files found")

    # No point in using more threads than files
    # if len(files_to_check) < num_procs:
    #     num_procs = len(files_to_check)

    results = _run_pylint(files_to_check, interactive)

    return results

    # pool = ThreadPool(num_procs)
    # results = pool.map(lambda x : _run_pylint(x, interactive), files_to_check)
    # pool.close()
    # pool.join()
    # return dict(results)
