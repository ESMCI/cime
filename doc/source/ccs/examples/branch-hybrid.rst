.. _ccs_examples_branch-hybrid:

Setting up a branch or hybrid run
---------------------------------
A branch or hybrid run uses initialization data from a previous run. Here is an example in which a valid load-balanced scenario is assumed.
This requires the :ref:`ccs_examples_multi-year` to have been ran and completed successfully.

1. The first step in setting up a branch or hybrid run is to create a new case.

     .. code-block:: bash
          
          ./scripts/create_newcase --case ~/BRANCH_HYBRID --compset B1850 --res f09_g17
          cd ~/BRANCH_HYBRID

2. Now to setup the branch/hybrid starting from year 0001-02-01 of the previous run.

     For a branch run, use the following ``xmlchange`` commands to make **NEW_CASE** be a branch off of **EXAMPLE_CASE** at year 0001-02-01.
     
     .. code-block:: bash
     
            ./xmlchange RUN_TYPE=branch
            ./xmlchange RUN_REFCASE=EXAMPLE_CASE
            ./xmlchange RUN_REFDATE=0001-02-01

     .. note::
          
          For a branch run, the **env_run.xml** file for **NEW_CASE** should be identical to the file for **EXAMPLE_CASE** except for the ``$RUN_TYPE`` setting.
          Also, modifications introduced into **user_nl_** files in **EXAMPLE_CASE** should be reintroduced in **NEW_CASE**.

     For a hybrid run, use the following ``xmlchange`` command to start **NEW_CASE** from **EXAMPLE_CASE** at year 0001-02-01.
     
     .. code-block:: bash

            ./xmlchange RUN_TYPE=hybrid
            ./xmlchange RUN_REFCASE=EXAMPLE_CASE
            ./xmlchange RUN_REFDATE=0001-02-01

4. Next, set up and build the case executable.
   
     .. code-block:: bash

        ./case.setup
        ./case.build

5. Pre-stage the necessary restart/initial data in ``$RUNDIR``. For this example the restart files are assumed to be in ``$DOUT_S_ROOT/EXAMPLE_CASE/rest/0001-02-01-00000``.

     .. code-block:: bash

        cp $DOUT_S_ROOT/EXAMPLE_CASE/rest/0001-02-01-00000/* $RUNDIR/

     It is assumed that you already have a valid load-balanced scenario.
     Set the job to run 12 model months, and submit the job.

     .. code-block:: bash

        ./xmlchange STOP_OPTION=nmonths
        ./xmlchange STOP_N=12
        ./xmlchange JOB_WALLCLOCK_TIME=06:00
        ./case.submit

6. Make sure the run succeeded and and then change the run to resubmit 10 times so it will run a total of 11 years (including the initial year), then resubmit the case.

     .. code-block:: bash

        ./xmlchange CONTINUE_RUN=TRUE
        ./xmlchange RESUBMIT=10
        ./case.submit

     .. node::

          By default only a single job will be submitted at a time, to change this use ``./case.submit --resubmit-immediate`` which will submit all jobs at once using batch dependencies.