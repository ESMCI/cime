"""
Base class for CIME system tests that involve doing multiple runs and comparing the base run (index=0)
with the subsequent runs (indices=1..N-1).

NOTE: Below is the flow of a multisubmit test.
Non-batch:
case_submit -> case_run     # PHASE 1
            -> case_run     # PHASE 2
            ...
            -> case_run     # PHASE N

batch:
case_submit -> case_run     # PHASE 1
case_run    -> case_submit
case_submit -> case_run     # PHASE 2
...
case_submit -> case_run     # PHASE N

In the __init__ method for your test, you MUST call
    SystemTestsCompareN.__init__
See the documentation of that method for details.

Classes that inherit from this are REQUIRED to implement the following method:

(1) _case_setup
    This method will be called to set up case i, where i==0 corresponds to the base case
    and i=={1,..N-1} corresponds to subsequent runs to be compared with the base.

In addition, they MAY require the following methods:

(1) _common_setup
    This method will be called to set up all cases. It should contain any setup
    that's needed in all cases. This is called before _case_setup_config

(2) _case_custom_prerun_action(self, i):
    Use this to do arbitrary actions immediately before running case i

(3) _case_custom_postrun_action(self, i):
    Use this to do arbitrary actions immediately after running case one
"""

from CIME.XML.standard_module_setup import *
from CIME.SystemTests.system_tests_common import SystemTestsCommon
from CIME.case import Case
from CIME.config import Config
from CIME.test_status import *

import shutil, os, glob

logger = logging.getLogger(__name__)


class SystemTestsCompareN(SystemTestsCommon):
    def __init__(
        self,
        case,
        N=2,
        separate_builds=False,
        run_suffixes=None,
        run_descriptions=None,
        multisubmit=False,
        ignore_fieldlist_diffs=False,
    ):
        """
        Initialize a SystemTestsCompareN object. Individual test cases that
        inherit from SystemTestsCompareN MUST call this __init__ method.

        Args:
            case: case object passsed to __init__ method of individual
                test. This is the main case associated with the test.
            N (int): number of test cases including the base case.
            separate_builds (bool): Whether separate builds are needed for the
                cases. If False, case[i:1..N-1] uses the case[0] executable.
            run_suffixes (list of str, optional): List of suffixes appended to the case names.
                Defaults to ["base", "subsq_1", "subsq_2", .. "subsq_N-1"]. Each
                suffix must be unique.
            run_descriptions (list of str, optional): Descriptions printed to log file
                of each case when starting the runs. Defaults to ['']*N.
            multisubmit (bool): Do base and subsequent runs as different submissions.
                Designed for tests with RESUBMIT=1
            ignore_fieldlist_diffs (bool): If True, then: If the cases differ only in
                their field lists (i.e., all shared fields are bit-for-bit, but one case
                has some diagnostic fields that are missing from the base case), treat
                the cases as identical. (This is needed for tests where one case
                exercises an option that produces extra diagnostic fields.)
        """
        SystemTestsCommon.__init__(self, case)

        self._separate_builds = separate_builds
        self._ignore_fieldlist_diffs = ignore_fieldlist_diffs

        expect(N > 1, "Number of cases must be greater than 1.")
        self._cases = [None] * N
        self.N = N

        if run_suffixes:
            expect(
                isinstance(run_suffixes, list)
                and all([isinstance(sfx, str) for sfx in run_suffixes]),
                "run_suffixes must be a list of strings",
            )
            expect(
                len(run_suffixes) == self.N,
                "run_suffixes list must include {} strings".format(self.N),
            )
            expect(
                len(set(run_suffixes)) == len(run_suffixes),
                "each suffix in run_suffixes must be unique",
            )
            self._run_suffixes = [sfx.rstrip() for sfx in run_suffixes]
        else:
            self._run_suffixes = ["base"] + ["subsq_{}".format(i) for i in range(1, N)]

        if run_descriptions:
            expect(
                isinstance(run_descriptions, list)
                and all([isinstance(dsc, str) for dsc in run_descriptions]),
                "run_descriptions must be a list of strings",
            )
            expect(
                len(run_descriptions) == self.N,
                "run_descriptions list must include {} strings".format(self.N),
            )
            self._run_descriptions = run_descriptions
        else:
            self._run_descriptions = [""] * self.N

        # Set the base case for referencing purposes
        self._cases[0] = self._case
        self._caseroots = self._get_caseroots()

        self._setup_cases_if_not_yet_done()

        self._multisubmit = (
            multisubmit and self._cases[0].get_value("BATCH_SYSTEM") != "none"
        )

    # ========================================================================
    # Methods that MUST be implemented by specific tests that inherit from this
    # base class
    # ========================================================================

    def _case_setup(self, i):
        """
        This method will be called to set up case[i], where case[0] is the base case.

        This should be written to refer to self._case: this object will point to
        case[i] at the point that this is called.
        """
        raise NotImplementedError

    # ========================================================================
    # Methods that MAY be implemented by specific tests that inherit from this
    # base class, if they have any work to do in these methods
    # ========================================================================

    def _common_setup(self):
        """
        This method will be called to set up all cases. It should contain any setup
        that's needed in both cases.

        This should be written to refer to self._case: It will be called once with
        self._case pointing to case1, and once with self._case pointing to case2.
        """

    def _case_custom_prerun_action(self, i):
        """
        Use to do arbitrary actions immediately before running case i:0..N
        """

    def _case_custom_postrun_action(self, i):
        """
        Use to do arbitrary actions immediately after running case i:0..N
        """

    # ========================================================================
    # Main public methods
    # ========================================================================

    def build_phase(self, sharedlib_only=False, model_only=False):
        # Subtle issue: base case is already in a writeable state since it tends to be opened
        # with a with statement in all the API entrances in CIME. subsequent cases were
        # created via clone, not a with statement, so it's not in a writeable state,
        # so we need to use a with statement here to put it in a writeable state.
        config = Config.instance()

        for i in range(1, self.N):
            with self._cases[i]:
                if self._separate_builds:
                    self._activate_case(0)
                    self.build_indv(
                        sharedlib_only=sharedlib_only, model_only=model_only
                    )
                    self._activate_case(i)
                    # Although we're doing separate builds, it still makes sense
                    # to share the sharedlibroot area with case1 so we can reuse
                    # pieces of the build from there.
                    if config.common_sharedlibroot:
                        # We need to turn off this change for E3SM because it breaks
                        # the MPAS build system
                        ## TODO: ^this logic mimics what's done in SystemTestsCompareTwo
                        # Confirm this is needed in SystemTestsCompareN as well.
                        self._cases[i].set_value(
                            "SHAREDLIBROOT", self._cases[0].get_value("SHAREDLIBROOT")
                        )

                    self.build_indv(
                        sharedlib_only=sharedlib_only, model_only=model_only
                    )
                else:
                    self._activate_case(0)
                    self.build_indv(
                        sharedlib_only=sharedlib_only, model_only=model_only
                    )
                    # pio_typename may be changed during the build if the default is not a
                    # valid value for this build, update case i to reflect this change
                    for comp in self._cases[i].get_values("COMP_CLASSES"):
                        comp_pio_typename = "{}_PIO_TYPENAME".format(comp)
                        self._cases[i].set_value(
                            comp_pio_typename,
                            self._cases[0].get_value(comp_pio_typename),
                        )

                    # The following is needed when _case_two_setup has a case_setup call
                    # despite sharing the build (e.g., to change NTHRDS)
                    self._cases[i].set_value("BUILD_COMPLETE", True)

    def run_phase(self, success_change=False):  # pylint: disable=arguments-differ
        """
        Runs all phases of the N-phase test and compares base results with subsequent ones
        If success_change is True, success requires some files to be different
        """
        is_first_run = self._cases[0].get_value("IS_FIRST_RUN")

        # On a batch system with a multisubmit test "RESUBMIT" is used to track
        # which phase is being ran. By the end of the test it equals 0. If the
        # the test fails in a way where the RUN_PHASE is PEND then "RESUBMIT"
        # does not get reset to 1 on a rerun and the first phase is skipped
        # causing the COMPARE_PHASE to fail. This ensures that "RESUBMIT" will
        # get reset if the test state is not correct for a rerun.
        # NOTE: "IS_FIRST_RUN" is reset in "case_submit.py"
        ### todo: confirm below code block
        if (
            is_first_run
            and self._multisubmit
            and self._cases[0].get_value("RESUBMIT") == 0
        ):
            self._resetup_case(RUN_PHASE, reset=True)

        base_phase = (
            self._cases[0].get_value("RESUBMIT") == 1
        )  # Only relevant for multi-submit tests
        run_type = self._cases[0].get_value("RUN_TYPE")

        logger.info(
            "_multisubmit {} first phase {}".format(self._multisubmit, base_phase)
        )

        # First run
        if not self._multisubmit or base_phase:
            logger.info("Doing first run: " + self._run_descriptions[0])

            # Add a PENDing compare phase so that we'll notice if the second part of compare two
            # doesn't run.
            compare_phase_name = "{}_{}_{}".format(
                COMPARE_PHASE, self._run_suffixes[1], self._run_suffixes[0]
            )
            with self._test_status:
                self._test_status.set_status(compare_phase_name, TEST_PEND_STATUS)

            self._activate_case(0)
            self._case_custom_prerun_action(0)
            self.run_indv(suffix=self._run_suffixes[0])
            self._case_custom_postrun_action(0)

        # Subsequent runs
        if not self._multisubmit or not base_phase:
            # Subtle issue: case1 is already in a writeable state since it tends to be opened
            # with a with statement in all the API entrances in CIME. subsq cases were created
            # via clone, not a with statement, so it's not in a writeable state, so we need to
            # use a with statement here to put it in a writeable state.
            for i in range(1, self.N):
                with self._cases[i]:
                    logger.info("Doing run {}: ".format(i) + self._run_descriptions[i])
                    self._activate_case(i)
                    # This assures that case i namelists are populated
                    self._skip_pnl = False
                    # we need to make sure run i is properly staged.
                    if run_type != "startup":
                        self._cases[i].check_case()

                    self._case_custom_prerun_action(i)
                    self.run_indv(suffix=self._run_suffixes[i])
                    self._case_custom_postrun_action(i)
                # Compare results
                self._activate_case(0)
                self._link_to_subsq_case_output(i)
                self._component_compare_test(
                    self._run_suffixes[i],
                    self._run_suffixes[0],
                    success_change=success_change,
                    ignore_fieldlist_diffs=self._ignore_fieldlist_diffs,
                )

    # ========================================================================
    # Private methods
    # ========================================================================

    def _get_caseroots(self):
        """
        Determines and returns caseroot for each cases and returns a list
        """
        casename_base = self._cases[0].get_value("CASE")
        caseroot_base = self._get_caseroot()

        return [caseroot_base] + [
            os.path.join(caseroot_base, "case{}".format(i), casename_base)
            for i in range(1, self.N)
        ]

    def _get_subsq_output_root(self, i):
        """
        Determines and returns cime_output_root for case i where i!=0

        Assumes that self._case1 is already set to point to the case1 object
        """
        # Since subsequent cases have the same name as base, their CIME_OUTPUT_ROOT
        # must also be different, so that anything put in
        # $CIME_OUTPUT_ROOT/$CASE/ is not accidentally shared between
        # cases. (Currently nothing is placed here, but this
        # helps prevent future problems.)

        expect(i != 0, "ERROR: cannot call _get_subsq_output_root for the base class")

        output_root_i = os.path.join(
            self._cases[0].get_value("CIME_OUTPUT_ROOT"),
            self._cases[0].get_value("CASE"),
            "case{}_output_root".format(i),
        )
        return output_root_i

    def _get_subsq_case_exeroot(self, i):
        """
        Gets exeroot for case i.

        Returns None if we should use the default value of exeroot.
        """

        expect(i != 0, "ERROR: cannot call _get_subsq_case_exeroot for the base class")

        if self._separate_builds:
            # subsequent case's EXEROOT needs to be somewhere that (1) is unique
            # to this case (considering that all cases have the
            # same case name), and (2) does not have too long of a path
            # name (because too-long paths can make some compilers
            # fail).
            base_exeroot = self._cases[0].get_value("EXEROOT")
            case_i_exeroot = os.path.join(base_exeroot, "case{}bld".format(i))
        else:
            # Use default exeroot
            case_i_exeroot = None
        return case_i_exeroot

    def _get_subsq_case_rundir(self, i):
        """
        Gets rundir for case i.
        """

        expect(i != 0, "ERROR: cannot call _get_subsq_case_rundir for the base class")

        # subsequent case's RUNDIR needs to be somewhere that is unique to this
        # case (considering that all cases have the same case
        # name). Note that the location below is symmetrical to the
        # location of case's EXEROOT set in _get_subsq_case_exeroot.
        base_rundir = self._cases[0].get_value("RUNDIR")
        case_i_rundir = os.path.join(base_rundir, "case{}run".format(i))
        return case_i_rundir

    def _setup_cases_if_not_yet_done(self):
        """
        Determines if subsequent cases already exist on disk. If they do, this method
        creates the self.cases entries pointing to the case directories. If they
        don't exist, then this method creates cases[i:1..N-1] as a clone of cases[0], and
        sets the self.cases objects appropriately.

        This also does the setup for all cases including the base case.

        Assumes that the following variables are already set in self:
            _caseroots
            _cases[0]

        Sets self.cases[i:1..N-1]
        """

        # Use the existence of the cases[N-1] directory to signal whether we have
        # done the necessary test setup for all cases: When we initially create
        # the last case directory, we set up all cases; then, if we find that
        # the last case directory already exists, we assume that the setup has
        # already been done for all cases. (In some cases it could be problematic
        # to redo the test setup when it's not needed - e.g., by appending things
        # to user_nl files multiple times. This is why we want to make sure to just
        # do the test setup once.)
        if os.path.exists(self._caseroots[-1]):
            for i in range(1, self.N):
                caseroot_i = self._caseroots[i]
                self._cases[i] = self._case_from_existing_caseroot(caseroot_i)
        else:
            # Create the subsequent cases by cloning the base case.
            for i in range(1, self.N):
                self._cases[i] = self._cases[0].create_clone(
                    self._caseroots[i],
                    keepexe=not self._separate_builds,
                    cime_output_root=self._get_subsq_output_root(i),
                    exeroot=self._get_subsq_case_exeroot(i),
                    rundir=self._get_subsq_case_rundir(i),
                )
                self._write_info_to_subsq_case_output_root(i)

            # Set up all cases, including the base case.
            for i in range(0, self.N):
                caseroot_i = self._caseroots[i]
                try:
                    self._setup_case(i)
                except BaseException:
                    # If a problem occurred in setting up the test case i, it's
                    # important to remove the case i directory: If it's kept around,
                    # that would signal that test setup was done successfully, and
                    # thus doesn't need to be redone - which is not the case. Of
                    # course, we'll likely be left in an inconsistent state in this
                    # case, but if we didn't remove the case i directory, the next
                    # re-build of the test would think, "okay, setup is done, I can
                    # move on to the build", which would be wrong.
                    if os.path.isdir(caseroot_i):
                        shutil.rmtree(caseroot_i)
                    self._activate_case(0)
                    logger.warning(
                        "WARNING: Test case setup failed. Case {} has been removed, "
                        "but the main case may be in an inconsistent state. "
                        "If you want to rerun this test, you should create "
                        "a new test rather than trying to rerun this one.".format(i)
                    )
                    raise

    def _case_from_existing_caseroot(self, caseroot):
        """
        Returns a Case object from an existing caseroot directory

        Args:
            caseroot (str): path to existing caseroot
        """
        return Case(case_root=caseroot, read_only=False)

    def _activate_case(self, i):
        """
        Make case i active for upcoming calls
        """
        os.chdir(self._caseroots[i])
        self._set_active_case(self._cases[i])

    def _write_info_to_subsq_case_output_root(self, i):
        """
        Writes a file with some helpful information to case[i]'s
        output_root.

        The motivation here is two-fold:

        (1) Currently, case i's output_root directory is empty.
            This could be confusing.

        (2) For users who don't know where to look, it could be hard to
            find case i's bld and run directories. It is somewhat easier
            to stumble upon case i output_root, so we put a file there
            pointing them to the right place.
        """

        readme_path = os.path.join(self._get_subsq_output_root(i), "README")
        try:
            with open(readme_path, "w") as fd:
                fd.write("This directory is typically empty.\n\n")
                fd.write(
                    "case's run dir is here: {}\n\n".format(
                        self._cases[i].get_value("RUNDIR")
                    )
                )
                fd.write(
                    "case's bld dir is here: {}\n".format(
                        self._cases[i].get_value("EXEROOT")
                    )
                )
        except IOError:
            # It's not a big deal if we can't write the README file
            # (e.g., because the directory doesn't exist or isn't
            # writeable; note that the former may be the case in unit
            # tests). So just continue merrily on our way if there was a
            # problem.
            pass

    def _setup_case(self, i):
        """
        Does all test-specific set up for the test case i.
        """

        # Set up case 1
        self._activate_case(i)
        self._common_setup()
        self._case_setup(i)
        if i == 0:
            # Flush the case so that, if errors occur later, then at least base case is
            # in a correct, post-setup state. This is important because the mere
            # existence of a cases[-1] directory signals that setup is done. So if the
            # build fails and the user rebuilds, setup won't be redone - so it's
            # important to ensure that the results of setup are flushed to disk.
            #
            # Note that base case will be in its post-setup state even if case[i!=0] setup fails.
            self._case.flush()
            # This assures that case one namelists are populated
            # and creates the case.test script
            self._case.case_setup(test_mode=False, reset=True)
        else:
            # Go back to base case to ensure that's where we are for any following code
            self._activate_case(0)

    def _link_to_subsq_case_output(self, i):
        """
        Looks for all files in rundir-i matching the pattern casename-i*.nc.run-i-suffix

        For each file found, makes a link in base rundir pointing to this file; the
        link is renamed so that the original occurrence of casename-i is replaced
        with base casename.

        For example:

        /glade/scratch/sacks/somecase/run/somecase.clm2.h0.nc.run2 ->
        /glade/scratch/sacks/somecase.run2/run/somecase.run2.clm2.h0.nc.run2

        If the destination link already exists and points to the correct
        location, it is maintained as is. However, an exception will be raised
        if the destination link is not exactly as it should be: we avoid
        overwriting some existing file or link.
        """

        expect(
            i != 0, "ERROR: cannot call _link_to_subsq_case_output for the base class"
        )

        base_casename = self._cases[0].get_value("CASE")
        subsq_casename = self._cases[i].get_value("CASE")
        base_rundir = self._cases[0].get_value("RUNDIR")
        subsq_rundir = self._cases[i].get_value("RUNDIR")

        pattern = "{}*.nc.{}".format(subsq_casename, self._run_suffixes[i])
        subsq_case_files = glob.glob(os.path.join(subsq_rundir, pattern))
        for one_file in subsq_case_files:
            file_basename = os.path.basename(one_file)
            modified_basename = file_basename.replace(subsq_casename, base_casename, 1)
            one_link = os.path.join(base_rundir, modified_basename)
            if os.path.islink(one_link) and os.readlink(one_link) == one_file:
                # Link is already set up correctly: do nothing
                # (os.symlink raises an exception if you try to replace an
                # existing file)
                pass
            else:
                os.symlink(one_file, one_link)
