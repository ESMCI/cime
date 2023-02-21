import CIME.compare_namelists, CIME.simple_compare
from CIME.test_scheduler import NAMELIST_PHASE
from CIME.utils import (
    run_cmd,
    get_scripts_root,
    EnvironmentContext,
    parse_test_name,
)
from CIME.config import Config
from CIME.test_status import *
from CIME.hist_utils import generate_baseline, compare_baseline
from CIME.case import Case
from CIME.test_utils import get_test_status_files
import os, time

logger = logging.getLogger(__name__)

###############################################################################
def bless_namelists(
    test_name,
    report_only,
    force,
    pesfile,
    baseline_name,
    baseline_root,
    new_test_root=None,
    new_test_id=None,
):
    ###############################################################################
    # Be aware that restart test will overwrite the original namelist files
    # with versions of the files that should not be blessed. This forces us to
    # re-run create_test.

    # Update namelist files
    logger.info("Test '{}' had namelist diff".format(test_name))
    if not report_only and (
        force or input("Update namelists (y/n)? ").upper() in ["Y", "YES"]
    ):
        config = Config.instance()

        create_test_gen_args = " -g {} ".format(
            baseline_name
            if config.create_test_flag_mode == "cesm"
            else " -g -b {} ".format(baseline_name)
        )
        if new_test_root is not None:
            create_test_gen_args += " --test-root={0} --output-root={0} ".format(
                new_test_root
            )
        if new_test_id is not None:
            create_test_gen_args += " -t {}".format(new_test_id)

        if pesfile is not None:
            create_test_gen_args += " --pesfile {}".format(pesfile)

        stat, out, _ = run_cmd(
            "{}/create_test {} --namelists-only {} --baseline-root {} -o".format(
                get_scripts_root(), test_name, create_test_gen_args, baseline_root
            ),
            combine_output=True,
        )
        if stat != 0:
            return False, "Namelist regen failed: '{}'".format(out)
        else:
            return True, None
    else:
        return True, None


###############################################################################
def bless_history(test_name, case, baseline_name, baseline_root, report_only, force):
    ###############################################################################
    real_user = case.get_value("REALUSER")
    with EnvironmentContext(USER=real_user):

        baseline_full_dir = os.path.join(
            baseline_root, baseline_name, case.get_value("CASEBASEID")
        )

        cmp_result, cmp_comments = compare_baseline(
            case, baseline_dir=baseline_full_dir, outfile_suffix=None
        )
        if cmp_result:
            logger.info("Diff appears to have been already resolved.")
            return True, None
        else:
            logger.info(cmp_comments)
            if not report_only and (
                force or input("Update this diff (y/n)? ").upper() in ["Y", "YES"]
            ):
                gen_result, gen_comments = generate_baseline(
                    case, baseline_dir=baseline_full_dir
                )
                if not gen_result:
                    logger.warning(
                        "Hist file bless FAILED for test {}".format(test_name)
                    )
                    return False, "Generate baseline failed: {}".format(gen_comments)
                else:
                    logger.info(gen_comments)
                    return True, None
            else:
                return True, None


###############################################################################
def bless_test_results(
    baseline_name,
    baseline_root,
    test_root,
    compiler,
    test_id=None,
    namelists_only=False,
    hist_only=False,
    report_only=False,
    force=False,
    pesfile=None,
    bless_tests=None,
    no_skip_pass=False,
    new_test_root=None,
    new_test_id=None,
):
    ###############################################################################
    test_status_files = get_test_status_files(test_root, compiler, test_id=test_id)

    # auto-adjust test-id if multiple rounds of tests were matched
    timestamps = set()
    for test_status_file in test_status_files:
        timestamp = os.path.basename(os.path.dirname(test_status_file)).split(".")[-1]
        timestamps.add(timestamp)

    if len(timestamps) > 1:
        logger.warning(
            "Multiple sets of tests were matched! Selected only most recent tests."
        )

    most_recent = sorted(timestamps)[-1]
    logger.info("Matched test batch is {}".format(most_recent))

    bless_tests_counts = None
    if bless_tests:
        bless_tests_counts = dict([(bless_test, 0) for bless_test in bless_tests])

    broken_blesses = []
    for test_status_file in test_status_files:
        if not most_recent in test_status_file:
            logger.info("Skipping {}".format(test_status_file))
            continue

        test_dir = os.path.dirname(test_status_file)
        ts = TestStatus(test_dir=test_dir)
        test_name = ts.get_name()
        testopts = parse_test_name(test_name)[1]
        testopts = [] if testopts is None else testopts
        build_only = "B" in testopts
        if test_name is None:
            case_dir = os.path.basename(test_dir)
            test_name = CIME.utils.normalize_case_id(case_dir)
            if not bless_tests or CIME.utils.match_any(test_name, bless_tests_counts):
                broken_blesses.append(
                    (
                        "unknown",
                        "test had invalid TestStatus file: '{}'".format(
                            test_status_file
                        ),
                    )
                )
                continue
            else:
                continue

        if bless_tests in [[], None] or CIME.utils.match_any(
            test_name, bless_tests_counts
        ):
            overall_result, phase = ts.get_overall_test_status(
                ignore_namelists=True, ignore_memleak=True
            )

            # See if we need to bless namelist
            if not hist_only:
                if no_skip_pass:
                    nl_bless = True
                else:
                    nl_bless = ts.get_status(NAMELIST_PHASE) != TEST_PASS_STATUS
            else:
                nl_bless = False

            # See if we need to bless baselines
            if not namelists_only and not build_only:
                run_result = ts.get_status(RUN_PHASE)
                if run_result is None:
                    broken_blesses.append((test_name, "no run phase"))
                    logger.warning(
                        "Test '{}' did not make it to run phase".format(test_name)
                    )
                    hist_bless = False
                elif run_result != TEST_PASS_STATUS:
                    broken_blesses.append((test_name, "run phase did not pass"))
                    logger.warning(
                        "Test '{}' run phase did not pass, not safe to bless, test status = {}".format(
                            test_name, ts.phase_statuses_dump()
                        )
                    )
                    hist_bless = False
                elif overall_result == TEST_FAIL_STATUS:
                    broken_blesses.append((test_name, "test did not pass"))
                    logger.warning(
                        "Test '{}' did not pass due to phase {}, not safe to bless, test status = {}".format(
                            test_name, phase, ts.phase_statuses_dump()
                        )
                    )
                    hist_bless = False

                elif no_skip_pass:
                    hist_bless = True
                else:
                    hist_bless = ts.get_status(BASELINE_PHASE) != TEST_PASS_STATUS
            else:
                hist_bless = False

            # Now, do the bless
            if not nl_bless and not hist_bless:
                logger.info(
                    "Nothing to bless for test: {}, overall status: {}".format(
                        test_name, overall_result
                    )
                )
            else:

                logger.info(
                    "###############################################################################"
                )
                logger.info(
                    "Blessing results for test: {}, most recent result: {}".format(
                        test_name, overall_result
                    )
                )
                logger.info("Case dir: {}".format(test_dir))
                logger.info(
                    "###############################################################################"
                )
                if not force:
                    time.sleep(2)

                with Case(test_dir) as case:
                    # Resolve baseline_name and baseline_root
                    if baseline_name is None:
                        baseline_name_resolved = case.get_value("BASELINE_NAME_CMP")
                        if not baseline_name_resolved:
                            baseline_name_resolved = CIME.utils.get_current_branch(
                                repo=CIME.utils.get_cime_root()
                            )
                    else:
                        baseline_name_resolved = baseline_name

                    if baseline_root is None:
                        baseline_root_resolved = case.get_value("BASELINE_ROOT")
                    else:
                        baseline_root_resolved = baseline_root

                    if baseline_name_resolved is None:
                        broken_blesses.append(
                            (test_name, "Could not determine baseline name")
                        )
                        continue

                    if baseline_root_resolved is None:
                        broken_blesses.append(
                            (test_name, "Could not determine baseline root")
                        )
                        continue

                    # Bless namelists
                    if nl_bless:
                        success, reason = bless_namelists(
                            test_name,
                            report_only,
                            force,
                            pesfile,
                            baseline_name_resolved,
                            baseline_root_resolved,
                            new_test_root=new_test_root,
                            new_test_id=new_test_id,
                        )
                        if not success:
                            broken_blesses.append((test_name, reason))

                    # Bless hist files
                    if hist_bless:
                        if "HOMME" in test_name:
                            success = False
                            reason = (
                                "HOMME tests cannot be blessed with bless_for_tests"
                            )
                        else:
                            success, reason = bless_history(
                                test_name,
                                case,
                                baseline_name_resolved,
                                baseline_root_resolved,
                                report_only,
                                force,
                            )

                        if not success:
                            broken_blesses.append((test_name, reason))

    # Emit a warning if items in bless_tests did not match anything
    if bless_tests:
        for bless_test, bless_count in bless_tests_counts.items():
            if bless_count == 0:
                logger.warning(
                    """
bless test arg '{}' did not match any tests in test_root {} with
compiler {} and test_id {}. It's possible that one of these arguments
had a mistake (likely compiler or testid).""".format(
                        bless_test, test_root, compiler, test_id
                    )
                )

    # Make sure user knows that some tests were not blessed
    success = True
    for broken_bless, reason in broken_blesses:
        logger.warning(
            "FAILED TO BLESS TEST: {}, reason {}".format(broken_bless, reason)
        )
        success = False

    return success
