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

.. list-table:: Main Variables
  :header-rows: 1

  * - Variable
    - Description
  * - cime_model
    - Name of the model to be used.
  * - project
    - The project identifier.
  * - charge_account
    - The account to be charged.
  * - srcroot
    - The root directory of the model source code.
  * - mail_type
    - The type of mail notifications (e.g., fail, all).
  * - mail_user
    - The user to receive mail notifications.
  * - machine
    - The machine to be used.
  * - mpilib
    - The MPI library to be used.
  * - compiler
    - The compiler to be used.
  * - input_dir
    - The directory for input files.
  * - cime_driver
    - The model driver to use.

Create Test
-----------
The following example shows setting defaults for the **create_test** script.

.. code-block:: ini

    [create_test]
    MAIL_TYPE=fail

.. list-table:: Create Test Variables
  :header-rows: 1

  * - Variable
    - Description
  * - mail_type
    - The type of mail notifications (e.g., fail, all).
  * - mail_user
    - The user to receive mail notifications.
  * - save_timing
    - Save timing information.
  * - single_submit
    - Submit all jobs as a single job.
  * - test_root
    - The root directory for tests.
  * - output_root
    - The root directory for output.
  * - baseline_root
    - The root directory for baselines.
  * - clean
    - Clean before running tests.
  * - machine
    - The machine to be used.
  * - mpilib
    - The MPI library to be used.
  * - compiler
    - The compiler to be used.
  * - parallel_jobs
    - The number of parallel jobs to run.
  * - proc_pool
    - The pool of processors to use.
  * - walltime
    - The wall time for the job.
  * - job_queue
    - The job queue to use.
  * - allow_baseline_overwrite
    - Allow overwriting of baselines.
  * - skip_tests_with_existing_baselines
    - Skip tests with existing baselines.
  * - wait
    - Wait for jobs to complete.
  * - force_procs
    - Force the number of processors.
  * - force_threads
    - Force the number of threads.
  * - input_dir
    - The directory for input files.
  * - pesfile
    - The file specifying processor layout.
  * - retry
    - The number of retries for failed tests.

Machine
```````
The user can define their own machine configuration by creating a ``$HOME/.cime/config_machines.xml`` file. See the :ref:`config_machines.xml<model_config_machines_def>` section for more information.

These additional machine entries will be appended to the entries provided by the model.

CMake macros
````````````
The user can define their own cmake macros by creating a ``$HOME/.cime/cmake_macros`` directory. See the :ref:`cmake_macros<model_config_cmake_macros_dir_def>` section for more information.

Compilers
`````````

.. warning::

  The creation of ``config_compilers.xml`` is **DEPRECATED**. Use the cmake_macros directory instead.

Batch System
`````````````
The user can define their own batch system configuration by creating a ``$HOME/.cime/config_batch.xml`` file. See the :ref:`config_batch.xml<model_config_batch_def>` section for more information.
