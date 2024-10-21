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

=================================  =======================  =====  ================================================================================================================================================================================================================================
Variable                           Default                  Type   Description                                                                                                                                                                                                                     
=================================  =======================  =====  ================================================================================================================================================================================================================================
additional_archive_components      ('drv', 'dart')          tuple  Additional components to archive.
allow_unsupported                  True                     bool   If set to `True` then unsupported compsets and resolutions are allowed.
baseline_store_teststatus          True                     bool   If set to `True` and GENERATE_BASELINE is set then a teststatus.log is created in the case's baseline.
build_cime_component_lib           True                     bool   If set to `True` then `Filepath`, `CIME_cppdefs` and `CCSM_cppdefs` directories are copied from CASEBUILD directory to BUILDROOT in order to build CIME's internal components.
build_model_use_cmake              False                    bool   If set to `True` the model is built using using CMake otherwise Make is used.
calculate_mode_build_cost          False                    bool   If set to `True` then the TestScheduler will set the number of processors for building the model to min(16, (($GMAKE_J * 2) / 3) + 1) otherwise it's set to 4.
case_setup_generate_namelist       False                    bool   If set to `True` and case is a test then namelists are created during `case.setup`.
check_invalid_args                 True                     bool   If set to `True` then script arguments are checked for being valid.
check_machine_name_from_test_name  True                     bool   If set to `True` then the TestScheduler will use testlists to parse for a list of tests.
common_sharedlibroot               True                     bool   If set to `True` then SHAREDLIBROOT is set for the case and SystemTests will only build the shared libs once.
copy_cesm_tools                    True                     bool   If set to `True` then CESM specific tools are copied into the case directory.
copy_cism_source_mods              True                     bool   If set to `True` then `$CASEROOT/SourceMods/src.cism/source_cism` is created and a README is written to directory.
copy_e3sm_tools                    False                    bool   If set to `True` then E3SM specific tools are copied into the case directory.
create_bless_log                   False                    bool   If set to `True` and comparing test to baselines the most recent bless is added to comments.
create_test_flag_mode              cesm                     str    Sets the flag mode for the `create_test` script. When set to `cesm`, the `-c` flag will compare baselines against a give directory.
default_short_term_archiving       True                     bool   If set to `True` and the case is not a test then DOUT_S is set to True and TIMER_LEVEL is set to 4.
driver_choices                     ('mct', 'nuopc')         tuple  Sets the available driver choices for the model.
driver_default                     nuopc                    str    Sets the default driver for the model.
enable_smp                         True                     bool   If set to `True` then `SMP=` is added to model compile command.
make_case_run_batch_script         False                    bool   If set to `True` and case is not a test then `case.run.sh` is created in case directory from `$MACHDIR/template.case.run.sh`.
mct_path                           {srcroot}/libraries/mct  str    Sets the path to the mct library.
serialize_sharedlib_builds         True                     bool   If set to `True` then the TestScheduler will use `proc_pool + 1` processors to build shared libraries otherwise a single processor is used.
set_comp_root_dir_cpl              True                     bool   If set to `True` then COMP_ROOT_DIR_CPL is set for the case.
share_exes                         False                    bool   If set to `True` then the TestScheduler will share exes between tests.
shared_clm_component               True                     bool   If set to `True` and then the `clm` land component is built as a shared lib.
sort_tests                         False                    bool   If set to `True` then the TestScheduler will sort tests by runtime.
test_custom_project_machine        melvin                   str    Sets the machine name to use when testing a machine with no PROJECT.
test_mode                          cesm                     str    Sets the testing mode, this changes various configuration for CIME's unit and system tests.
ufs_alternative_config             False                    bool   If set to `True` and UFS_DRIVER is set to `nems` then model config dir is set to `$CIMEROOT/../src/model/NEMS/cime/cime_config`.
use_kokkos                         False                    bool   If set to `True` and CAM_TARGET is `preqx_kokkos`, `theta-l` or `theta-l_kokkos` then kokkos is built with the shared libs.
use_nems_comp_root_dir             False                    bool   If set to `True` then COMP_ROOT_DIR_CPL is set using UFS_DRIVER if defined.
use_testreporter_template          True                     bool   If set to `True` then the TestScheduler will create `testreporter` in $CIME_OUTPUT_ROOT.
verbose_run_phase                  False                    bool   If set to `True` then after a SystemTests successful run phase the elapsed time is recorded to BASELINE_ROOT, on a failure the test is checked against the previous run and potential breaking merges are listed in the testlog.
xml_component_key                  COMP_ROOT_DIR_{}         str    The string template used as the key to query the XML system to find a components root directory e.g. the template `COMP_ROOT_DIR_{}` and component `LND` becomes `COMP_ROOT_DIR_LND`.
=================================  =======================  =====  ================================================================================================================================================================================================================================

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
