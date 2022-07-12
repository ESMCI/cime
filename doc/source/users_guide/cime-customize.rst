.. _customizing-cime:

===========================
CIME config and hooks
===========================

CIME provides the ability to define model specific config and hooks.

The config alters CIME's runtime and the hooks are triggered during their event.

-----------------------------------
How does CIME load customizations?
-----------------------------------

CIME will search ``cime_config/customize`` and load any python found under this directory or it's children.

Any variables, functions or classes loaded are available from the ``CIME.customize`` module.

---------------------------
CIME config
---------------------------

Available config and descriptions.

=================================  ================  ====  =============================================================================================================================================================
Variable                           Default           Type  Description                                                                                                                                                  
=================================  ================  ====  =============================================================================================================================================================
allow_unsupported                  True              bool  Allows creation of case that is not test or supported.
archive_dart_component             True              bool  Archives dart component.
archive_drv_component              True              bool  Archives drv component.
baseline_store_teststatus          True              bool  Upon the completion of a SystemTest and GENERATE_BASELINE is True, the TestStatus will be copied from the case directory to the baseline directory.
build_cime_component_lib           True              bool  Build CIME component lib.
build_model_use_cmake              False             bool  When building model use CMake.
calculate_mode_build_cost          False             bool  Calculates model build cost rather than using static value in test_scheduler
case_setup_generate_namelist       False             bool  Creates namelist during case.setup for some tests.
cesm_create_test_flags             True              bool  Enables CESM specific `create_test` flags.
check_invalid_args                 True              bool  Validates arguments when parsing for CIME commands.
check_machine_name_from_test_name  True              bool  Try to get machine name from testname.
common_sharedlibroot               True              bool  During BUILD phase of a SystemTestsCompareN SHAREDLIBROOT is set the same for all cases.
copy_cesm_tools                    True              bool  Copies archive_metadata to case root.
copy_cism_source_mods              True              bool  Copies cism SourceMods.
copy_e3sm_tools                    False             bool  Copies E3SM specific tools to case tools.
create_bless_log                   False             bool  Creates a bless log when comparing baseline.
default_short_term_archiving       True              bool  Forces short term archiving when not a test.
enable_smp                         True              bool  Enables SMP when building model.
gpus_use_set_device_rank           True              bool  Uses set_device_rank.sh from RUNDIR when composing MPI run command.
make_case_run_batch_script         False             bool  Makes case.run batch script during case setup.
serialize_sharedlib_builds         True              bool  Test scheduler will serialize sharedlib builds.
set_comp_root_dir_cpl              True              bool  Sets COMP_ROOT_DIR_CPL when setting compset.
share_exes                         False             bool  Test scheduler will shared exes.
shared_clm_component               True              bool  Enables shared clm component.
skip_cdash_tests                   True              bool  Skips E3SM CDASH tests.
skip_checksum_tests                False             bool  Skips CESM checksum tests.
skip_gen_domain_tests              True              bool  Skips E3SM gen_domain tests.
skip_jenkins_tests                 True              bool  Skips E3SM jenkins tests.
skip_performance_archive_tests     True              bool  Skips E3SM performance archiving tests.
skip_print_compset                 False             bool  Skip printing compset.
skip_single_submit_test            True              bool  Skip single submit tests.
skip_success_recording_tests       True              bool  Skips E3SM success recording tests.
skip_walltime_tests                True              bool  Skips E3SM specific walltime tests.
skip_xml_test_management_tests     False             bool  Skips non E3SM XML test management tests.
sort_tests                         False             bool  When creating a test if walltime is defined tests are sorted by execution time
test_custom_project_machine        melvin            str   Set a machine which doesn't use PROJECT for testing.
ufs_alternative_config             False             bool  Enables ufs config_dir for `nems` driver.
use_kokkos                         False             bool  Enables use of kokkos, CAM_TARGET must be set to either `preqx_kokkos`, `theta-l` or `theta-l_kokkos`.
use_nems_comp_root_dir             False             bool  Use nems specific value for COMP_ROOT_DIR_CPL.
use_testreporter_template          True              bool  Test scheduler will use testreporter.template.
verbose_run_phase                  False             bool  Upon a successful SystemTest, the time taken is recorded to the BASELINE_ROOT. If the RUN phase failed then a possible explanation is appened to the testlog.
xml_component_key                  COMP_ROOT_DIR_{}  str   Component key used whenm querying config.
=================================  ================  ====  =============================================================================================================================================================

---------------------------
CIME hooks
---------------------------

Available hooks and descriptions.

=======================================  =================================
Function                                 Description
=======================================  =================================
``save_build_provenance(case, lid)``     Called after the model is built.
``save_prerun_provenance(case, lid)``    Called before the model is run.
``save_postrun_provenance(case, lid)``   Called after the model is run.
=======================================  =================================
