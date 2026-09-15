.. _ccs_examples_multi-year:

Setting up a multi-year run
---------------------------
This example will show how to set up a multi-year simulation start from a "cold start" for all components using CIME. It is assumed that 
you have already set up your environment and have a working CIME installation.

1. Create a new case named ``EXAMPLE_CASE`` in your ``$HOME`` directory.

      .. code-block:: bash
            
            ./scripts/create_newcase --case $HOME/EXAMPLE_CASE --compset B1850 --res f09_g17

2. Check the pe-layout using ``./pelayout``. Make sure it is suitable for your machine. If it is not use ``xmlchange`` or ``pelayout`` to modify your pe-layout.
   Then setup your case and build your executable.

      .. code-block:: bash

            cd ~/EXAMPLE_CASE
            ./case.setup
            ./case.build

      .. warning:: The case.build script can be compute intensive and may not be suitable to run on a login node. As an alternative you would submit this job to an interactive queue.

3. In your case directory, set the job to run 12 model months, set the wallclock time, and submit the job.

      .. code-block:: bash

            ./xmlchange STOP_OPTION=nmonths
            ./xmlchange STOP_N=12
            ./xmlchange JOB_WALLCLOCK_TIME=06:00 --subgroup case.run
            ./case.submit

4. Make sure the run succeeded by check the ``CaseStatus`` file in your case directory. You can also check the log files in the **rundir** directory.

      .. code-block:: bash

            grep "case.run success" CaseStatus

      or

      .. code-block:: bash

            zgrep "SUCCESSFUL" run/cpl.log*

5. To generate additional years, the ``RESUBMIT`` variable will need to be set to the desired number of years to run.  In this example it will be set to 10,
      which will generate a total of 11 years (including the initial year).

      .. code-block:: bash

            ./xmlchange RESUBMIT=10
            ./case.submit

   By default resubmitted runs are not submitted until the previous run is completed, there will only be one job in the queue at a time.
   To change this behavior, and submit all jobs at once using batch dependencies use the following command:

      .. code-block:: bash

            ./case.submit --resubmit-immediate