#!/usr/bin/env python3

"""
Library for saving build/run provenance.
"""

from CIME.XML.standard_module_setup import *
from CIME.utils import (
    SharedArea,
    convert_to_babylonian_time,
    get_current_commit,
    run_cmd,
)

import sys

logger = logging.getLogger(__name__)


_WALLTIME_BASELINE_NAME = "walltimes"
_WALLTIME_FILE_NAME = "walltimes"
_GLOBAL_MINUMUM_TIME = 900
_GLOBAL_WIGGLE = 1000
_WALLTIME_TOLERANCE = ((600, 2.0), (1800, 1.5), (9999999999, 1.25))


def get_recommended_test_time_based_on_past(baseline_root, test, raw=False):
    if baseline_root is not None:
        try:
            the_path = os.path.join(
                baseline_root, _WALLTIME_BASELINE_NAME, test, _WALLTIME_FILE_NAME
            )
            if os.path.exists(the_path):
                last_line = int(open(the_path, "r").readlines()[-1].split()[0])
                if raw:
                    best_walltime = last_line
                else:
                    best_walltime = None
                    for cutoff, tolerance in _WALLTIME_TOLERANCE:
                        if last_line <= cutoff:
                            best_walltime = int(float(last_line) * tolerance)
                            break

                    if best_walltime < _GLOBAL_MINUMUM_TIME:
                        best_walltime = _GLOBAL_MINUMUM_TIME

                    best_walltime += _GLOBAL_WIGGLE

                return convert_to_babylonian_time(best_walltime)
        except Exception:
            # We NEVER want a failure here to kill the run
            logger.warning("Failed to read test time: {}".format(sys.exc_info()[1]))

    return None


def save_test_time(baseline_root, test, time_seconds, commit):
    if baseline_root is not None:
        try:
            with SharedArea():
                the_dir = os.path.join(baseline_root, _WALLTIME_BASELINE_NAME, test)
                if not os.path.exists(the_dir):
                    os.makedirs(the_dir)

                the_path = os.path.join(the_dir, _WALLTIME_FILE_NAME)
                with open(the_path, "a") as fd:
                    fd.write("{} {}\n".format(int(time_seconds), commit))

        except Exception:
            # We NEVER want a failure here to kill the run
            logger.warning("Failed to store test time: {}".format(sys.exc_info()[1]))


_SUCCESS_BASELINE_NAME = "success-history"
_SUCCESS_FILE_NAME = "last-transitions"


def _read_success_data(baseline_root, test):
    success_path = os.path.join(
        baseline_root, _SUCCESS_BASELINE_NAME, test, _SUCCESS_FILE_NAME
    )
    if os.path.exists(success_path):
        with open(success_path, "r") as fd:
            prev_results_raw = fd.read().strip()
            prev_results = prev_results_raw.split()
            expect(
                len(prev_results) == 2,
                "Bad success data: '{}'".format(prev_results_raw),
            )
    else:
        prev_results = ["None", "None"]

    # Convert "None" to None
    for idx, item in enumerate(prev_results):
        if item == "None":
            prev_results[idx] = None

    return success_path, prev_results


def _is_test_working(prev_results, src_root, testing=False):
    # If there is no history of success, prev run could not have succeeded and vice versa for failures
    if prev_results[0] is None:
        return False
    elif prev_results[1] is None:
        return True
    else:
        if not testing:
            stat, out, err = run_cmd(
                "git merge-base --is-ancestor {}".format(" ".join(prev_results)),
                from_dir=src_root,
            )
            expect(
                stat in [0, 1],
                "Unexpected status from ancestor check:\n{}\n{}".format(out, err),
            )
        else:
            # Hack for testing
            stat = 0 if prev_results[0] < prev_results[1] else 1

        # stat == 0 tells us that pass is older than fail, so we must have failed, otherwise we passed
        return stat != 0


def get_test_success(baseline_root, src_root, test, testing=False):
    """
    Returns (was prev run success, commit when test last passed, commit when test last transitioned from pass to fail)

    Unknown history is expressed as None
    """
    if baseline_root is not None:
        try:
            prev_results = _read_success_data(baseline_root, test)[1]
            prev_success = _is_test_working(prev_results, src_root, testing=testing)
            return prev_success, prev_results[0], prev_results[1]

        except Exception:
            # We NEVER want a failure here to kill the run
            logger.warning("Failed to read test success: {}".format(sys.exc_info()[1]))

    return False, None, None


def save_test_success(baseline_root, src_root, test, succeeded, force_commit_test=None):
    """
    Update success data accordingly based on succeeded flag
    """
    if baseline_root is not None:
        try:
            with SharedArea():
                success_path, prev_results = _read_success_data(baseline_root, test)

                the_dir = os.path.dirname(success_path)
                if not os.path.exists(the_dir):
                    os.makedirs(the_dir)

                prev_succeeded = _is_test_working(
                    prev_results, src_root, testing=(force_commit_test is not None)
                )

                # if no transition occurred then no update is needed
                if (
                    succeeded
                    or succeeded != prev_succeeded
                    or (prev_results[0] is None and succeeded)
                    or (prev_results[1] is None and not succeeded)
                ):

                    new_results = list(prev_results)
                    my_commit = (
                        force_commit_test
                        if force_commit_test
                        else get_current_commit(repo=src_root)
                    )
                    if succeeded:
                        new_results[0] = my_commit  # we passed
                    else:
                        new_results[1] = my_commit  # we transitioned to a failing state

                    str_results = [
                        "None" if item is None else item for item in new_results
                    ]
                    with open(success_path, "w") as fd:
                        fd.write("{}\n".format(" ".join(str_results)))

        except Exception:
            # We NEVER want a failure here to kill the run
            logger.warning("Failed to store test success: {}".format(sys.exc_info()[1]))
