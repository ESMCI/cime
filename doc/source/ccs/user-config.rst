.. _ccs_user_config:

User Config
===========

.. contents::
  :local:

CIME provides a mechanism for users to customize their CCS environment by creating a ``$HOME/.cime`` directory. This directory can contain a number of files that will be used to customize the CCS environment. The following sections describe the files that can be placed in the ``$HOME/.cime`` directory.

Configuration
-------------
The user can set defaults by creating a ``$HOME/.cime/config`` file. This file must follow the Python config format.

Main
`````
Variables can be defined in the **[main]** section of the config file.

.. code-block:: ini

   [main]
   CIME_MODEL=<model>
   PROJECT=<project>
   MAIL_TYPE=<mail_type>
   SRCROOT=<srcroot>

=================== ==============================
Variable            Description
=================== ==============================
cime_model          Name of the model to be used.
PROJECT             The project identifier.
CHARGE_ACCOUNT      The account to be charged.
SRCROOT             The root directory of the model source code.
MAIL_TYPE           The type of mail notifications (e.g., fail, all).
MAIL_USER           The user to receive mail notifications.
MACHINE             The machine to be used.
MPILIB              The MPI library to be used.
COMPILER            The compiler to be used.
INPUT_DIR           The directory for input files.
CIME_DRIVER         The model driver to use.
=================== ==============================

Create Test
```````````
The following example shows setting defaults for the **create_test** script.

.. code-block:: ini

    [create_test]
    MAIL_TYPE=fail

===================================== ================================================
Variable                              Description
===================================== ================================================
MAIL_TYPE                             The type of mail notifications (e.g., fail, all).
MAIL_USER                             The user to receive mail notifications.
SAVE_TIMING                           Save timing information.
SINGLE_SUBMIT                         Submit all jobs as a single job.
TEST_ROOT                             The root directory for tests.
OUTPUT_ROOT                           The root directory for output.
BASELINE_ROOT                         The root directory for baselines.
CLEAN                                 Clean before running tests.
MACHINE                               The machine to be used.
MPILIB                                The MPI library to be used.
COMPILER                              The compiler to be used.
PARALLEL_JOBS                         The number of parallel jobs to run.
PROC_POOL                             The pool of processors to use.
WALLTIME                              The wall time for the job.
JOB_QUEUE                             The job queue to use.
ALLOW_BASELINE_OVERWRITE              Allow overwriting of baselines.
SKIP_TESTS_WITH_EXISTING_BASELINES    Skip tests with existing baselines.
WAIT                                  Wait for jobs to complete.
FORCE_PROCS                           Force the number of processors.
FORCE_THREADS                         Force the number of threads.
INPUT_DIR                             The directory for input files.
PESFILE                               The file specifying processor layout.
RETRY                                 The number of retries for failed tests.
===================================== ================================================

Machine
-------
The user can define their own machine configuration by creating a ``$HOME/.cime/config_machines.xml`` file. See the :ref:`config_machines.xml<model_config_machines_def>` section for more information.

These additional machine entries will be appended to the entries provided by the model.

CMake macros
------------
The user can define their own cmake macros by creating a ``$HOME/.cime/cmake_macros`` directory. See the :ref:`cmake_macros<model_config_cmake_macros_dir_def>` section for more information.

Batch System
------------
The user can define their own batch system configuration by creating a ``$HOME/.cime/config_batch.xml`` file. See the :ref:`config_batch.xml<model_config_batch_def>` section for more information.
