"""
Base class for CIME system tests
"""

from CIME.XML.standard_module_setup import *
from CIME.XML.env_run import EnvRun
from CIME.XML.env_test import EnvTest
from CIME.status import append_testlog
from CIME.utils import (
    get_model,
    safe_copy,
    get_timestamp,
    CIMEError,
    expect,
    get_current_commit,
    SharedArea,
    is_comp_standalone,
)
from CIME.test_status import *
from CIME.hist_utils import (
    copy_histfiles,
    compare_test,
    generate_teststatus,
    compare_baseline,
    get_ts_synopsis,
    generate_baseline,
)
from CIME.config import Config
from CIME.provenance import save_test_time, get_test_success
from CIME.locked_files import LOCKED_DIR, lock_file, is_locked
from CIME.baselines.performance import (
    get_latest_cpl_logs,
    perf_get_memory_list,
    perf_compare_memory_baseline,
    perf_compare_throughput_baseline,
    perf_write_baseline,
    load_coupler_customization,
)
import CIME.build as build

import glob, gzip, time, traceback, os, math
from contextlib import ExitStack

logger = logging.getLogger(__name__)

# Name of directory under the run directory in which init-generated files are placed
INIT_GENERATED_FILES_DIRNAME = "init_generated_files"


def fix_single_exe_case(case):
    """Fixes cases created with --single-exe.

    When tests are created using --single-exe, the test_scheduler will set
    `BUILD_COMPLETE` to True, but some tests require calls to `case.case_setup`
    which can resets `BUILD_COMPLETE` to false. This function will check if a
    case was created with `--single-exe` and ensure `BUILD_COMPLETE` is True.

    Returns:
        True when case required modification otherwise False.
    """
    if is_single_exe_case(case):
        with ExitStack() as stack:
            # enter context if case is still read-only, entering the context
            # multiple times can cause side effects for later calls to
            # `set_value` when it's assumed the cause is writeable.
            if case._read_only_mode:
                stack.enter_context(case)

            case.set_value("BUILD_COMPLETE", True)

            return True

    return False


def is_single_exe_case(case):
    """Determines if the case was created with the --single-exe option.

    If `CASEROOT` is not part of `EXEROOT` and the `TEST` variable is True,
    then its safe to assume the case was created with `./create_test`
    and the `--single-exe` option.

    Returns:
        True when the case was created with `--single-exe` otherwise false.
    """
    caseroot = case.get_value("CASEROOT")

    exeroot = case.get_value("EXEROOT")

    test = case.get_value("TEST")

    return caseroot not in exeroot and test


class SystemTestsCommon(object):
    def __init__(
        self, case, expected=None, **kwargs
    ):  # pylint: disable=unused-argument
        """
        initialize a CIME system test object, if the locked env_run.orig.xml
        does not exist copy the current env_run.xml file.  If it does exist restore values
        changed in a previous run of the test.
        """
        self._case = case
        caseroot = case.get_value("CASEROOT")
        self._caseroot = caseroot
        self._orig_caseroot = caseroot
        self._runstatus = None
        self._casebaseid = self._case.get_value("CASEBASEID")
        self._test_status = TestStatus(test_dir=caseroot, test_name=self._casebaseid)
        self._init_environment(caseroot)
        self._init_locked_files(caseroot, expected)
        self._skip_pnl = False
        self._cpllog = (
            "med" if self._case.get_value("COMP_INTERFACE") == "nuopc" else "cpl"
        )
        self._ninja = False
        self._dry_run = False
        self._user_separate_builds = False
        self._expected_num_cmp = None
        self._rest_n = None

    def _set_restart_interval(self):
        stop_n = self._case.get_value("STOP_N")
        stop_option = self._case.get_value("STOP_OPTION")
        self._case.set_value("REST_OPTION", stop_option)
        # We need to make sure the run is long enough and to set REST_N to a
        # value that makes sense for all components
        maxncpl = 10000
        minncpl = 0
        for comp in self._case.get_values("COMP_CLASSES"):
            if comp == "CPL":
                continue
            compname = self._case.get_value("COMP_{}".format(comp))

            # ignore stub components in this test.
            if compname == "s{}".format(comp.lower()):
                ncpl = None
            else:
                ncpl = self._case.get_value("{}_NCPL".format(comp))

            if ncpl and maxncpl > ncpl:
                maxncpl = ncpl
            if ncpl and minncpl < ncpl:
                minncpl = ncpl

        ncpl_base_period = self._case.get_value("NCPL_BASE_PERIOD")
        if ncpl_base_period == "hour":
            coupling_secs = 3600 / maxncpl
            timestep = 3600 / minncpl
        elif ncpl_base_period == "day":
            coupling_secs = 86400 / maxncpl
            timestep = 86400 / minncpl
        elif ncpl_base_period == "year":
            coupling_secs = 31536000 / maxncpl
            timestep = 31536000 / minncpl
        elif ncpl_base_period == "decade":
            coupling_secs = 315360000 / maxncpl
            timestep = 315360000 / minncpl

        # Convert stop_n to units of coupling intervals
        factor = 1
        if stop_option == "nsteps":
            factor = timestep
        elif stop_option == "nminutes":
            factor = 60
        elif stop_option == "nhours":
            factor = 3600
        elif stop_option == "ndays":
            factor = 86400
        elif stop_option == "nyears":
            factor = 315360000
        else:
            expect(False, f"stop_option {stop_option} not available for this test")

        stop_n = int(stop_n * factor // coupling_secs)
        rest_n = math.ceil((stop_n // 2 + 1) * coupling_secs / factor)

        expect(stop_n > 0, "Bad STOP_N: {:d}".format(stop_n))

        expect(stop_n > 2, "ERROR: stop_n value {:d} too short".format(stop_n))
        logger.info(
            "doing an {0} {1} initial test with restart file at {2} {1}".format(
                str(stop_n), stop_option, str(rest_n)
            )
        )
        self._case.set_value("REST_N", rest_n)
        return rest_n

    def _init_environment(self, caseroot):
        """
        Do initializations of environment variables that are needed in __init__
        """
        # Needed for sh scripts
        os.environ["CASEROOT"] = caseroot

    def _init_locked_files(self, caseroot, expected):
        """
        If the locked env_run.orig.xml does not exist, copy the current
        env_run.xml file. If it does exist, restore values changed in a previous
        run of the test.
        """
        if is_locked("env_run.orig.xml", caseroot):
            self.compare_env_run(expected=expected)
        elif os.path.isfile(os.path.join(caseroot, "env_run.xml")):
            lock_file("env_run.xml", caseroot, newname="env_run.orig.xml")

    def _resetup_case(self, phase, reset=False):
        """
        Re-setup this case. This is necessary if user is re-running an already-run
        phase.
        """
        # We never want to re-setup if we're doing the resubmitted run
        phase_status = self._test_status.get_status(phase)
        phase_comment = self._test_status.get_comment(phase)
        rerunning = (
            phase_status != TEST_PEND_STATUS or phase_comment == TEST_RERUN_COMMENT
        )
        if reset or (self._case.get_value("IS_FIRST_RUN") and rerunning):

            logging.warning(
                "Resetting case due to detected re-run of phase {}".format(phase)
            )
            self._case.set_initial_test_values()
            self._case.case_setup(reset=True, test_mode=True)
            fix_single_exe_case(self._case)

    def build(
        self,
        sharedlib_only=False,
        model_only=False,
        ninja=False,
        dry_run=False,
        separate_builds=False,
        skip_submit=False,
    ):
        """
        Do NOT override this method, this method is the framework that
        controls the build phase. build_phase is the extension point
        that subclasses should use.
        """
        success = True
        self._ninja = ninja
        self._dry_run = dry_run
        self._user_separate_builds = separate_builds

        was_run_pend = self._test_status.current_is(RUN_PHASE, TEST_PEND_STATUS)

        for phase_name, phase_bool in [
            (SHAREDLIB_BUILD_PHASE, not model_only),
            (MODEL_BUILD_PHASE, not sharedlib_only),
        ]:
            if phase_bool:
                self._resetup_case(phase_name)
                with self._test_status:
                    self._test_status.set_status(phase_name, TEST_PEND_STATUS)

                start_time = time.time()
                try:
                    self.build_phase(
                        sharedlib_only=(phase_name == SHAREDLIB_BUILD_PHASE),
                        model_only=(phase_name == MODEL_BUILD_PHASE),
                    )
                except BaseException as e:  # We want KeyboardInterrupts to generate FAIL status
                    success = False
                    if isinstance(e, CIMEError):
                        # Don't want to print stacktrace for a build failure since that
                        # is not a CIME/infrastructure problem.
                        excmsg = str(e)
                    else:
                        excmsg = "Exception during build:\n{}\n{}".format(
                            str(e), traceback.format_exc()
                        )

                    append_testlog(excmsg, self._orig_caseroot)
                    raise

                finally:
                    time_taken = time.time() - start_time
                    with self._test_status:
                        self._test_status.set_status(
                            phase_name,
                            TEST_PASS_STATUS if success else TEST_FAIL_STATUS,
                            comments=("time={:d}".format(int(time_taken))),
                        )

        # Building model while job is queued and awaiting run
        if (
            skip_submit
            and was_run_pend
            and self._test_status.current_is(SUBMIT_PHASE, TEST_PEND_STATUS)
        ):
            with self._test_status:
                self._test_status.set_status(SUBMIT_PHASE, TEST_PASS_STATUS)

        return success

    def build_phase(self, sharedlib_only=False, model_only=False):
        """
        This is the default build phase implementation, it just does an individual build.
        This is the subclass' extension point if they need to define a custom build
        phase.

        PLEASE THROW EXCEPTION ON FAIL
        """
        self.build_indv(sharedlib_only=sharedlib_only, model_only=model_only)

    def build_indv(self, sharedlib_only=False, model_only=False):
        """
        Perform an individual build
        """
        model = self._case.get_value("MODEL")
        build.case_build(
            self._caseroot,
            case=self._case,
            sharedlib_only=sharedlib_only,
            model_only=model_only,
            save_build_provenance=not model == "cesm",
            ninja=self._ninja,
            dry_run=self._dry_run,
            separate_builds=self._user_separate_builds,
        )
        logger.info("build_indv complete")

    def clean_build(self, comps=None):
        if comps is None:
            comps = [x.lower() for x in self._case.get_values("COMP_CLASSES")]
        build.clean(self._case, cleanlist=comps)

    def run(self, skip_pnl=False):
        """
        Do NOT override this method, this method is the framework that controls
        the run phase. run_phase is the extension point that subclasses should use.
        """
        success = True
        start_time = time.time()
        self._skip_pnl = skip_pnl
        try:
            self._resetup_case(RUN_PHASE)
            do_baseline_ops = True
            with self._test_status:
                self._test_status.set_status(RUN_PHASE, TEST_PEND_STATUS)

            # We do not want to do multiple repetitions of baseline operations for
            # multi-submit tests. We just want to do them upon the final submission.
            # Other submissions will need to mark those phases as PEND to ensure wait_for_tests
            # waits for them.
            if self._case.get_value("BATCH_SYSTEM") != "none":
                do_baseline_ops = self._case.get_value("RESUBMIT") == 0

            self.run_phase()
            if self._case.get_value("GENERATE_BASELINE"):
                if do_baseline_ops:
                    self._phase_modifying_call(GENERATE_PHASE, self._generate_baseline)
                else:
                    with self._test_status:
                        self._test_status.set_status(GENERATE_PHASE, TEST_PEND_STATUS)

            if self._case.get_value("COMPARE_BASELINE"):
                if do_baseline_ops:
                    self._phase_modifying_call(BASELINE_PHASE, self._compare_baseline)
                    comp_standalone, _ = is_comp_standalone(self._case)
                    if not comp_standalone:
                        self._phase_modifying_call(MEMCOMP_PHASE, self._compare_memory)
                        self._phase_modifying_call(
                            THROUGHPUT_PHASE, self._compare_throughput
                        )
                else:
                    with self._test_status:
                        self._test_status.set_status(BASELINE_PHASE, TEST_PEND_STATUS)
                        self._test_status.set_status(MEMCOMP_PHASE, TEST_PEND_STATUS)
                        self._test_status.set_status(THROUGHPUT_PHASE, TEST_PEND_STATUS)

            self._phase_modifying_call(MEMLEAK_PHASE, self._check_for_memleak)
            self._phase_modifying_call(STARCHIVE_PHASE, self._st_archive_case_test)

        except BaseException as e:  # We want KeyboardInterrupts to generate FAIL status
            success = False
            if isinstance(e, CIMEError):
                # Don't want to print stacktrace for a model failure since that
                # is not a CIME/infrastructure problem.
                excmsg = str(e)
            else:
                excmsg = "Exception during run:\n{}\n{}".format(
                    str(e), traceback.format_exc()
                )

            append_testlog(excmsg, self._orig_caseroot)
            raise

        finally:
            # Writing the run status should be the very last thing due to wait_for_tests
            time_taken = time.time() - start_time
            status = TEST_PASS_STATUS if success else TEST_FAIL_STATUS
            with self._test_status:
                self._test_status.set_status(
                    RUN_PHASE, status, comments=("time={:d}".format(int(time_taken)))
                )

            config = Config.instance()

            if config.verbose_run_phase:
                # If run phase worked, remember the time it took in order to improve later walltime ests
                baseline_root = self._case.get_value("BASELINE_ROOT")
                if success:
                    srcroot = self._case.get_value("SRCROOT")
                    save_test_time(
                        baseline_root,
                        self._casebaseid,
                        time_taken,
                        get_current_commit(repo=srcroot),
                    )

                # If overall things did not pass, offer the user some insight into what might have broken things
                overall_status = self._test_status.get_overall_test_status(
                    ignore_namelists=True
                )[0]
                if overall_status != TEST_PASS_STATUS:
                    srcroot = self._case.get_value("SRCROOT")
                    worked_before, last_pass, last_fail_transition = get_test_success(
                        baseline_root, srcroot, self._casebaseid
                    )

                    if worked_before:
                        if last_pass is not None:
                            # commits between last_pass and now broke things
                            stat, out, err = run_cmd(
                                "git rev-list --first-parent {}..{}".format(
                                    last_pass, "HEAD"
                                ),
                                from_dir=srcroot,
                            )
                            if stat == 0:
                                append_testlog(
                                    "NEW FAIL: Potentially broken merges:\n{}".format(
                                        out
                                    ),
                                    self._orig_caseroot,
                                )
                            else:
                                logger.warning(
                                    "Unable to list potentially broken merges: {}\n{}".format(
                                        out, err
                                    )
                                )
                    else:
                        if last_pass is not None and last_fail_transition is not None:
                            # commits between last_pass and last_fail_transition broke things
                            stat, out, err = run_cmd(
                                "git rev-list --first-parent {}..{}".format(
                                    last_pass, last_fail_transition
                                ),
                                from_dir=srcroot,
                            )
                            if stat == 0:
                                append_testlog(
                                    "OLD FAIL: Potentially broken merges:\n{}".format(
                                        out
                                    ),
                                    self._orig_caseroot,
                                )
                            else:
                                logger.warning(
                                    "Unable to list potentially broken merges: {}\n{}".format(
                                        out, err
                                    )
                                )

            if config.baseline_store_teststatus and self._case.get_value(
                "GENERATE_BASELINE"
            ):
                baseline_dir = os.path.join(
                    self._case.get_value("BASELINE_ROOT"),
                    self._case.get_value("BASEGEN_CASE"),
                )
                generate_teststatus(self._caseroot, baseline_dir)

        # We return success if the run phase worked; memleaks, diffs will NOT be taken into account
        # with this return value.
        return success

    def run_phase(self):
        """
        This is the default run phase implementation, it just does an individual run.
        This is the subclass' extension point if they need to define a custom run phase.

        PLEASE THROW AN EXCEPTION ON FAIL
        """
        self.run_indv()

    def _get_caseroot(self):
        """
        Returns the current CASEROOT value
        """
        return self._caseroot

    def _set_active_case(self, case):
        """
        Use for tests that have multiple cases
        """
        self._case = case
        self._case.load_env(reset=True)
        self._caseroot = case.get_value("CASEROOT")

    def run_indv(
        self,
        suffix="base",
        st_archive=False,
        submit_resubmits=None,
        keep_init_generated_files=False,
    ):
        """
        Perform an individual run. Raises an EXCEPTION on fail.

        keep_init_generated_files: If False (the default), we remove the
        init_generated_files subdirectory of the run directory before running the case.
        This is usually what we want for tests, but some specific tests may want to leave
        this directory in place, so can set this variable to True to do so.
        """
        stop_n = self._case.get_value("STOP_N")
        stop_option = self._case.get_value("STOP_OPTION")
        run_type = self._case.get_value("RUN_TYPE")
        rundir = self._case.get_value("RUNDIR")
        try:
            self._case.check_all_input_data()
        except CIMEError:
            caseroot = self._case.get_value("CASEROOT")
            raise CIMEError(
                "Could not find all inputdata on any server, try "
                "manually running `./check_input_data --download "
                f"--verbose` from {caseroot!r}."
            ) from None
        if submit_resubmits is None:
            do_resub = self._case.get_value("BATCH_SYSTEM") != "none"
        else:
            do_resub = submit_resubmits

        # remove any cprnc output leftover from previous runs
        for compout in glob.iglob(os.path.join(rundir, "*.cprnc.out")):
            os.remove(compout)

        if not keep_init_generated_files:
            # remove all files in init_generated_files directory if it exists
            init_generated_files_dir = os.path.join(
                rundir, INIT_GENERATED_FILES_DIRNAME
            )
            if os.path.isdir(init_generated_files_dir):
                for init_file in glob.iglob(
                    os.path.join(init_generated_files_dir, "*")
                ):
                    os.remove(init_file)

        infostr = "doing an {:d} {} {} test".format(stop_n, stop_option, run_type)

        rest_option = self._case.get_value("REST_OPTION")
        if rest_option == "none" or rest_option == "never":
            infostr += ", no restarts written"
        else:
            rest_n = self._case.get_value("REST_N")
            infostr += ", with restarts every {:d} {}".format(rest_n, rest_option)

        logger.info(infostr)

        self._case.case_run(skip_pnl=self._skip_pnl, submit_resubmits=do_resub)

        if not self._coupler_log_indicates_run_complete():
            expect(False, "Coupler did not indicate run passed")

        if suffix is not None:
            self._component_compare_copy(suffix)

        if st_archive:
            self._case.case_st_archive(resubmit=True)

    def _coupler_log_indicates_run_complete(self):
        newestcpllogfiles = get_latest_cpl_logs(self._case)
        logger.debug("Latest Coupler log file(s) {}".format(newestcpllogfiles))
        # Exception is raised if the file is not compressed
        allgood = len(newestcpllogfiles)
        for cpllog in newestcpllogfiles:
            try:
                if b"SUCCESSFUL TERMINATION" in gzip.open(cpllog, "rb").read():
                    allgood = allgood - 1
            except Exception as e:  # Probably want to be more specific here
                msg = e.__str__()

                logger.info(
                    "{} is not compressed, assuming run failed {}".format(cpllog, msg)
                )

        return allgood == 0

    def _component_compare_copy(self, suffix):
        # Only match .nc files
        comments, num_copied = copy_histfiles(self._case, suffix, match_suffix="nc")
        self._expected_num_cmp = num_copied

        append_testlog(comments, self._orig_caseroot)

    def _log_cprnc_output_tail(self, filename_pattern, prepend=None):
        rundir = self._case.get_value("RUNDIR")

        glob_pattern = "{}/{}".format(rundir, filename_pattern)

        cprnc_logs = glob.glob(glob_pattern)

        for output in cprnc_logs:
            with open(output) as fin:
                cprnc_log_tail = fin.readlines()[-20:]

            cprnc_log_tail.insert(0, "tail -n20 {}\n\n".format(output))

            if prepend is not None:
                cprnc_log_tail.insert(0, "{}\n\n".format(prepend))

            append_testlog("".join(cprnc_log_tail), self._orig_caseroot)

    def _component_compare_test(
        self, suffix1, suffix2, success_change=False, ignore_fieldlist_diffs=False
    ):
        """
        Return value is not generally checked, but is provided in case a custom
        run case needs indirection based on success.
        If success_change is True, success requires some files to be different.
        If ignore_fieldlist_diffs is True, then: If the two cases differ only in their
            field lists (i.e., all shared fields are bit-for-bit, but one case has some
            diagnostic fields that are missing from the other case), treat the two cases
            as identical.
        """
        success, comments, num_compared = self._do_compare_test(
            suffix1, suffix2, ignore_fieldlist_diffs=ignore_fieldlist_diffs
        )
        if success_change:
            success = not success

        if (
            self._expected_num_cmp is not None
            and num_compared is not None
            and self._expected_num_cmp != num_compared
        ):
            comments = comments.replace("PASS", "")
            comments += """\nWARNING
Expected to compare {} hist files, but only compared {}. It's possible
that the hist_file_extension entry in config_archive.xml is not correct
for some of your components.
""".format(
                self._expected_num_cmp, num_compared
            )

        append_testlog(comments, self._orig_caseroot)

        pattern = "*.nc.{}.cprnc.out".format(suffix1)
        message = "compared suffixes suffix1 {!r} suffix2 {!r}".format(suffix1, suffix2)

        self._log_cprnc_output_tail(pattern, message)

        status = TEST_PASS_STATUS if success else TEST_FAIL_STATUS
        with self._test_status:
            self._test_status.set_status(
                "{}_{}_{}".format(COMPARE_PHASE, suffix1, suffix2), status
            )
        return success

    def _do_compare_test(self, suffix1, suffix2, ignore_fieldlist_diffs=False):
        """
        Wraps the call to compare_test to facilitate replacement in unit
        tests
        """
        return compare_test(
            self._case, suffix1, suffix2, ignore_fieldlist_diffs=ignore_fieldlist_diffs
        )

    def _st_archive_case_test(self):
        result = self._case.test_env_archive()
        with self._test_status:
            if result:
                self._test_status.set_status(STARCHIVE_PHASE, TEST_PASS_STATUS)
            else:
                self._test_status.set_status(STARCHIVE_PHASE, TEST_FAIL_STATUS)

    def _phase_modifying_call(self, phase, function):
        """
        Ensures that unexpected exceptions from phases will result in a FAIL result
        in the TestStatus file for that phase.
        """
        try:
            function()
        except Exception as e:  # Do NOT want to catch KeyboardInterrupt
            msg = e.__str__()
            excmsg = "Exception during {}:\n{}\n{}".format(
                phase, msg, traceback.format_exc()
            )

            logger.warning(excmsg)
            append_testlog(excmsg, self._orig_caseroot)

            with self._test_status:
                self._test_status.set_status(
                    phase, TEST_FAIL_STATUS, comments="exception"
                )

    def _check_for_memleak(self):
        """
        Examine memory usage as recorded in the cpl log file and look for unexpected
        increases.
        """
        config = load_coupler_customization(self._case)

        # default to 0.1
        tolerance = self._case.get_value("TEST_MEMLEAK_TOLERANCE") or 0.1

        expect(tolerance > 0.0, "Bad value for memleak tolerance in test")

        with self._test_status:
            try:
                memleak, comment = config.perf_check_for_memory_leak(
                    self._case, tolerance
                )
            except AttributeError:
                memleak, comment = perf_check_for_memory_leak(self._case, tolerance)

            if memleak:
                append_testlog(comment, self._orig_caseroot)

                status = TEST_FAIL_STATUS
            else:
                status = TEST_PASS_STATUS

            self._test_status.set_status(MEMLEAK_PHASE, status, comments=comment)

    def compare_env_run(self, expected=None):
        """
        Compare env_run file to original and warn about differences
        """
        components = self._case.get_values("COMP_CLASSES")
        f1obj = self._case.get_env("run")
        f2obj = EnvRun(
            self._caseroot,
            os.path.join(LOCKED_DIR, "env_run.orig.xml"),
            components=components,
        )
        diffs = f1obj.compare_xml(f2obj)
        for key in diffs.keys():
            if expected is not None and key in expected:
                logging.warning("  Resetting {} for test".format(key))
                f1obj.set_value(key, f2obj.get_value(key, resolved=False))
            else:
                print(
                    "WARNING: Found difference in test {}: case: {} original value {}".format(
                        key, diffs[key][0], diffs[key][1]
                    )
                )
                return False
        return True

    def _compare_memory(self):
        """
        Compares current test memory usage to baseline.
        """
        with self._test_status:
            try:
                below_tolerance, comment = perf_compare_memory_baseline(self._case)
            except Exception as e:
                logger.info("Failed to compare memory usage baseline: {!s}".format(e))

                self._test_status.set_status(
                    MEMCOMP_PHASE, TEST_FAIL_STATUS, comments=str(e)
                )
            else:
                if below_tolerance is not None:
                    append_testlog(comment, self._orig_caseroot)

                    if (
                        below_tolerance
                        and self._test_status.get_status(MEMCOMP_PHASE) is None
                    ):
                        self._test_status.set_status(MEMCOMP_PHASE, TEST_PASS_STATUS)
                    elif (
                        self._test_status.get_status(MEMCOMP_PHASE) != TEST_FAIL_STATUS
                    ):
                        self._test_status.set_status(
                            MEMCOMP_PHASE, TEST_FAIL_STATUS, comments=comment
                        )

    def _compare_throughput(self):
        """
        Compares current test throughput to baseline.
        """
        with self._test_status:
            try:
                below_tolerance, comment = perf_compare_throughput_baseline(self._case)
            except Exception as e:
                logger.info("Failed to compare throughput baseline: {!s}".format(e))

                self._test_status.set_status(
                    THROUGHPUT_PHASE, TEST_FAIL_STATUS, comments=str(e)
                )
            else:
                if below_tolerance is not None:
                    append_testlog(comment, self._orig_caseroot)

                    if (
                        below_tolerance
                        and self._test_status.get_status(THROUGHPUT_PHASE) is None
                    ):
                        self._test_status.set_status(THROUGHPUT_PHASE, TEST_PASS_STATUS)
                    elif (
                        self._test_status.get_status(THROUGHPUT_PHASE)
                        != TEST_FAIL_STATUS
                    ):
                        self._test_status.set_status(
                            THROUGHPUT_PHASE, TEST_FAIL_STATUS, comments=comment
                        )

    def _compare_baseline(self):
        """
        compare the current test output to a baseline result
        """
        with self._test_status:
            # compare baseline
            success, comments = compare_baseline(self._case)

            append_testlog(comments, self._orig_caseroot)

            pattern = "*.nc.cprnc.out"

            self._log_cprnc_output_tail(pattern)

            status = TEST_PASS_STATUS if success else TEST_FAIL_STATUS
            baseline_name = self._case.get_value("BASECMP_CASE")
            ts_comments = (
                os.path.dirname(baseline_name) + ": " + get_ts_synopsis(comments)
            )
            self._test_status.set_status(BASELINE_PHASE, status, comments=ts_comments)

    def _generate_baseline(self):
        """
        generate a new baseline case based on the current test
        """
        with self._test_status:
            # generate baseline
            success, comments = generate_baseline(self._case)
            append_testlog(comments, self._orig_caseroot)
            status = TEST_PASS_STATUS if success else TEST_FAIL_STATUS
            baseline_name = self._case.get_value("BASEGEN_CASE")
            self._test_status.set_status(
                GENERATE_PHASE, status, comments=os.path.dirname(baseline_name)
            )
            basegen_dir = os.path.join(
                self._case.get_value("BASELINE_ROOT"),
                self._case.get_value("BASEGEN_CASE"),
            )
            # copy latest cpl log to baseline
            # drop the date so that the name is generic
            newestcpllogfiles = get_latest_cpl_logs(self._case)
            with SharedArea():
                # TODO ever actually more than one cpl log?
                for cpllog in newestcpllogfiles:
                    m = re.search(r"/({}.*.log).*.gz".format(self._cpllog), cpllog)

                    if m is not None:
                        baselog = os.path.join(basegen_dir, m.group(1)) + ".gz"

                        safe_copy(
                            cpllog,
                            os.path.join(basegen_dir, baselog),
                            preserve_meta=False,
                        )

                        perf_write_baseline(self._case, basegen_dir, cpllog)


def perf_check_for_memory_leak(case, tolerance):
    leak = False
    comment = ""

    latestcpllogs = get_latest_cpl_logs(case)

    for cpllog in latestcpllogs:
        try:
            memlist = perf_get_memory_list(case, cpllog)
        except RuntimeError:
            return False, "insufficient data for memleak test"

        # last day - second day, skip first day, can be too low while initializing
        elapsed_days = int(memlist[-1][0]) - int(memlist[1][0])

        finalmem, originalmem = float(memlist[-1][1]), float(memlist[1][1])

        memdiff = -1 if originalmem <= 0 else (finalmem - originalmem) / originalmem

        if memdiff < 0:
            leak = False
            comment = "data for memleak test is insufficient"
        elif memdiff < tolerance:
            leak = False
            comment = ""
        else:
            leak = True
            comment = (
                "memleak detected, memory went from {:f} to {:f} in {:d} days".format(
                    originalmem, finalmem, elapsed_days
                )
            )

    return leak, comment


class FakeTest(SystemTestsCommon):
    """
    Inheriters of the FakeTest Class are intended to test the code.

    All members of the FakeTest Class must
    have names beginning with "TEST" this is so that the find_system_test
    in utils.py will work with these classes.
    """

    def __init__(self, case, expected=None, **kwargs):
        super(FakeTest, self).__init__(case, expected=expected, **kwargs)
        self._script = None
        self._requires_exe = False
        self._case._non_local = True
        self._original_exe = self._case.get_value("run_exe")

    def _set_script(self, script, requires_exe=False):
        self._script = script
        self._requires_exe = requires_exe

    def _resetup_case(self, phase, reset=False):
        run_exe = self._case.get_value("run_exe")
        super(FakeTest, self)._resetup_case(phase, reset=reset)
        self._case.set_value("run_exe", run_exe)

    def build_phase(self, sharedlib_only=False, model_only=False):
        if self._requires_exe:
            super(FakeTest, self).build_phase(
                sharedlib_only=sharedlib_only, model_only=model_only
            )

        if not sharedlib_only:
            exeroot = self._case.get_value("EXEROOT")
            modelexe = os.path.join(exeroot, "fake.exe")
            self._case.set_value("run_exe", modelexe)

            with open(modelexe, "w") as f:
                f.write("#!/bin/bash\n")
                f.write(self._script)

            os.chmod(modelexe, 0o755)

            if not self._requires_exe:
                build.post_build(self._case, [], build_complete=True)
            else:
                expect(
                    os.path.exists(modelexe),
                    "Could not find expected file {}".format(modelexe),
                )
                logger.info(
                    "FakeTest build_phase complete {} {}".format(
                        modelexe, self._requires_exe
                    )
                )

    def run_indv(
        self,
        suffix="base",
        st_archive=False,
        submit_resubmits=None,
        keep_init_generated_files=False,
    ):
        mpilib = self._case.get_value("MPILIB")
        # This flag is needed by mpt to run a script under mpiexec
        if mpilib == "mpt":
            os.environ["MPI_SHEPHERD"] = "true"
        super(FakeTest, self).run_indv(
            suffix, st_archive=st_archive, submit_resubmits=submit_resubmits
        )


class TESTRUNPASS(FakeTest):
    def build_phase(self, sharedlib_only=False, model_only=False):
        rundir = self._case.get_value("RUNDIR")
        cimeroot = self._case.get_value("CIMEROOT")
        case = self._case.get_value("CASE")
        script = """
echo Insta pass
echo SUCCESSFUL TERMINATION > {rundir}/{log}.log.$LID
cp {root}/scripts/tests/cpl.hi1.nc.test {rundir}/{case}.cpl.hi.0.nc
""".format(
            rundir=rundir, log=self._cpllog, root=cimeroot, case=case
        )
        self._set_script(script)
        FakeTest.build_phase(self, sharedlib_only=sharedlib_only, model_only=model_only)


class TESTRUNDIFF(FakeTest):
    """
    You can generate a diff with this test as follows:
    1) Run the test and generate a baseline
    2) set TESTRUNDIFF_ALTERNATE environment variable to TRUE
    3) Re-run the same test from step 1 but do a baseline comparison instead of generation
      3.a) This should give you a DIFF
    """

    def build_phase(self, sharedlib_only=False, model_only=False):
        rundir = self._case.get_value("RUNDIR")
        cimeroot = self._case.get_value("CIMEROOT")
        case = self._case.get_value("CASE")
        script = """
echo Insta pass
echo SUCCESSFUL TERMINATION > {rundir}/{log}.log.$LID
if [ -z "$TESTRUNDIFF_ALTERNATE" ]; then
  cp {root}/scripts/tests/cpl.hi1.nc.test {rundir}/{case}.cpl.hi.0.nc
else
  cp {root}/scripts/tests/cpl.hi2.nc.test {rundir}/{case}.cpl.hi.0.nc
fi
""".format(
            rundir=rundir, log=self._cpllog, root=cimeroot, case=case
        )
        self._set_script(script)
        FakeTest.build_phase(self, sharedlib_only=sharedlib_only, model_only=model_only)


class TESTRUNDIFFRESUBMIT(TESTRUNDIFF):
    pass


class TESTTESTDIFF(FakeTest):
    def build_phase(self, sharedlib_only=False, model_only=False):
        rundir = self._case.get_value("RUNDIR")
        cimeroot = self._case.get_value("CIMEROOT")
        case = self._case.get_value("CASE")
        script = """
echo Insta pass
echo SUCCESSFUL TERMINATION > {rundir}/{log}.log.$LID
cp {root}/scripts/tests/cpl.hi1.nc.test {rundir}/{case}.cpl.hi.0.nc
cp {root}/scripts/tests/cpl.hi2.nc.test {rundir}/{case}.cpl.hi.0.nc.rest
""".format(
            rundir=rundir, log=self._cpllog, root=cimeroot, case=case
        )
        self._set_script(script)
        super(TESTTESTDIFF, self).build_phase(
            sharedlib_only=sharedlib_only, model_only=model_only
        )

    def run_phase(self):
        super(TESTTESTDIFF, self).run_phase()
        self._component_compare_test("base", "rest")


class TESTRUNFAIL(FakeTest):
    def build_phase(self, sharedlib_only=False, model_only=False):
        rundir = self._case.get_value("RUNDIR")
        cimeroot = self._case.get_value("CIMEROOT")
        case = self._case.get_value("CASE")
        script = """
if [ -z "$TESTRUNFAIL_PASS" ]; then
  echo Insta fail
  echo model failed > {rundir}/{log}.log.$LID
  exit -1
else
  echo Insta pass
  echo SUCCESSFUL TERMINATION > {rundir}/{log}.log.$LID
  cp {root}/scripts/tests/cpl.hi1.nc.test {rundir}/{case}.cpl.hi.0.nc
fi
""".format(
            rundir=rundir, log=self._cpllog, root=cimeroot, case=case
        )
        self._set_script(script)
        FakeTest.build_phase(self, sharedlib_only=sharedlib_only, model_only=model_only)


class TESTRUNFAILRESET(TESTRUNFAIL):
    """This fake test can fail for two reasons:
    1. As in the TESTRUNFAIL test: If the environment variable TESTRUNFAIL_PASS is *not* set
    2. Even if that environment variable *is* set, it will fail if STOP_N differs from the
       original value

    The purpose of (2) is to ensure that test's values get properly reset if the test is
    rerun after an initial failure.
    """

    def run_indv(
        self,
        suffix="base",
        st_archive=False,
        submit_resubmits=None,
        keep_init_generated_files=False,
    ):
        # Make sure STOP_N matches the original value for the case. This tests that STOP_N
        # has been reset properly if we are rerunning the test after a failure.
        env_test = EnvTest(self._get_caseroot())
        stop_n = self._case.get_value("STOP_N")
        stop_n_test = int(env_test.get_test_parameter("STOP_N"))
        expect(
            stop_n == stop_n_test,
            "Expect STOP_N to match original ({} != {})".format(stop_n, stop_n_test),
        )

        # Now modify STOP_N so that an error will be generated if it isn't reset properly
        # upon a rerun
        self._case.set_value("STOP_N", stop_n + 1)

        super(TESTRUNFAILRESET, self).run_indv(
            suffix=suffix, st_archive=st_archive, submit_resubmits=submit_resubmits
        )


class TESTRUNFAILEXC(TESTRUNPASS):
    def run_phase(self):
        raise RuntimeError("Exception from run_phase")


class TESTRUNSTARCFAIL(TESTRUNPASS):
    def _st_archive_case_test(self):
        raise RuntimeError("Exception from st archive")


class TESTBUILDFAIL(TESTRUNPASS):
    def build_phase(self, sharedlib_only=False, model_only=False):
        if "TESTBUILDFAIL_PASS" in os.environ:
            TESTRUNPASS.build_phase(self, sharedlib_only, model_only)
        else:
            if not sharedlib_only:
                blddir = self._case.get_value("EXEROOT")
                bldlog = os.path.join(
                    blddir,
                    "{}.bldlog.{}".format(get_model(), get_timestamp("%y%m%d-%H%M%S")),
                )
                with open(bldlog, "w") as fd:
                    fd.write("BUILD FAIL: Intentional fail for testing infrastructure")

                expect(False, "BUILD FAIL: Intentional fail for testing infrastructure")


class TESTBUILDFAILEXC(FakeTest):
    def __init__(self, case, **kwargs):
        FakeTest.__init__(self, case, **kwargs)
        raise RuntimeError("Exception from init")


class TESTRUNUSERXMLCHANGE(FakeTest):
    def build_phase(self, sharedlib_only=False, model_only=False):
        caseroot = self._case.get_value("CASEROOT")
        modelexe = self._case.get_value("run_exe")
        new_stop_n = self._case.get_value("STOP_N") * 2

        script = """
cd {caseroot}
./xmlchange --file env_test.xml STOP_N={stopn}
./xmlchange RESUBMIT=1,STOP_N={stopn},CONTINUE_RUN=FALSE,RESUBMIT_SETS_CONTINUE_RUN=FALSE
cd -
{originalexe} "$@"
cd {caseroot}
./xmlchange run_exe={modelexe}
sleep 5
""".format(
            originalexe=self._original_exe,
            caseroot=caseroot,
            modelexe=modelexe,
            stopn=str(new_stop_n),
        )
        self._set_script(script, requires_exe=True)
        FakeTest.build_phase(self, sharedlib_only=sharedlib_only, model_only=model_only)

    def run_phase(self):
        self.run_indv(submit_resubmits=True)


class TESTRUNSLOWPASS(FakeTest):
    def build_phase(self, sharedlib_only=False, model_only=False):
        rundir = self._case.get_value("RUNDIR")
        cimeroot = self._case.get_value("CIMEROOT")
        case = self._case.get_value("CASE")
        script = """
sleep 300
echo Slow pass
echo SUCCESSFUL TERMINATION > {rundir}/{log}.log.$LID
cp {root}/scripts/tests/cpl.hi1.nc.test {rundir}/{case}.cpl.hi.0.nc
""".format(
            rundir=rundir, log=self._cpllog, root=cimeroot, case=case
        )
        self._set_script(script)
        FakeTest.build_phase(self, sharedlib_only=sharedlib_only, model_only=model_only)


class TESTMEMLEAKFAIL(FakeTest):
    def build_phase(self, sharedlib_only=False, model_only=False):
        rundir = self._case.get_value("RUNDIR")
        cimeroot = self._case.get_value("CIMEROOT")
        case = self._case.get_value("CASE")
        testfile = os.path.join(cimeroot, "scripts", "tests", "cpl.log.failmemleak.gz")
        script = """
echo Insta pass
gunzip -c {testfile} > {rundir}/{log}.log.$LID
cp {root}/scripts/tests/cpl.hi1.nc.test {rundir}/{case}.cpl.hi.0.nc
""".format(
            testfile=testfile, rundir=rundir, log=self._cpllog, root=cimeroot, case=case
        )
        self._set_script(script)
        FakeTest.build_phase(self, sharedlib_only=sharedlib_only, model_only=model_only)


class TESTMEMLEAKPASS(FakeTest):
    def build_phase(self, sharedlib_only=False, model_only=False):
        rundir = self._case.get_value("RUNDIR")
        cimeroot = self._case.get_value("CIMEROOT")
        case = self._case.get_value("CASE")
        testfile = os.path.join(cimeroot, "scripts", "tests", "cpl.log.passmemleak.gz")
        script = """
echo Insta pass
gunzip -c {testfile} > {rundir}/{log}.log.$LID
cp {root}/scripts/tests/cpl.hi1.nc.test {rundir}/{case}.cpl.hi.0.nc
""".format(
            testfile=testfile, rundir=rundir, log=self._cpllog, root=cimeroot, case=case
        )
        self._set_script(script)
        FakeTest.build_phase(self, sharedlib_only=sharedlib_only, model_only=model_only)
