.. _troubleshooting:

Troubleshooting
===============

Troubleshooting case creation
-----------------------------

Generally, **create_newcase** errors are reported to the terminal and should provide some guidance about what caused the error.

If **create_newcase** fails on a relatively generic error, first check carefully that the command line arguments match the interfaces specification. Type:
::

   > create_newcase --help

and review usage.

Troubleshooting job submission
-------------------------------

Most of the problems associated with submission or launch are very site specific.
The batch and run aspects of the ``case.submit`` script is created by parsing the xml variables in ``$CASEROOT/env_batch.xml``. 

First, review the batch submission options being used. These are found in ``$CASEROOT/env_batch.xml``. 
Confirm that the options are consistent with the site specific batch environment, and that the queue names, time limits, and hardware processor request makes sense and is consistent with the case running.

Second, make sure that ``case.submit`` submits the script ``case.run`` with the correct batch job submission tool, whether that's qsub, bsub, or something else, and for instance, whether a redirection "<" character is required or not.
The information for how ``case.submit`` submit jobs appears at the end of the standard output stream.

Troubleshooting run-time problems
---------------------------------

To check that a run completed successfully, check the last several lines of the cpl.log file for the string ``SUCCESSFUL TERMINATION OF CPL7-CCSM``. A successful job also usually copies the log files to the directory $CASEROOT/logs.

**Note**: The first things to check if a job fails are:
- whether the model timed out
- whether a disk quota limit was hit 
- whether a machine went down,
- whether a file system became full. 

If any of those things happened, take appropriate corrective action and resubmit the job.

If it is not clear any of the above caused a case to fail, then there are several places to look for error messages.

- Check component log files in ``$RUNDIR``.
  This directory is set in the ``env_run.xml`` and is where the model is run.
  Each component writes its own log file, and there should be log files there for every component (i.e. of the form cpl.log.yymmdd-hhmmss). 
  Check log file for each component for an error message, especially at the end or near the end of each file.

- Check for a standard out and/or standard error file in ``$CASEROOT``.
  The standard out/err file often captures a significant amount of extra model output and also often contains significant system output when the job terminates. 
  Sometimes, a useful error message can be found well above the bottom of a large standard out/err file. 
  Backtrack from the bottom in search of an error message.

- Check for core files in $RUNDIR and review them using an appropriate tool.

- Check any automated email from the job about why a job failed. This is sent by the batch scheduler and is a site specific feature that may or may not exist.

- Check the archive directory. 
  If a case failed, the log files or data may still have been archived. 
  The archiver is turned on if DOUT_S is set to TRUE in env_run.xml. 
  The archive directory is set by the env variable DOUT_S_ROOT and the directory to check is $DOUT_S_ROOT/$CASE.

A common error is for the job to time out which often produces minimal error messages. 
By reviewing the daily model date stamps in the cpl.log file and the time stamps of files in the $RUNDIR directory, there should be enough information to deduce the start and stop time of a run. 
If the model was running fine, but the batch wall limit was reached, either reduce the run length or increase the batch time limit request. 
If the model hangs and then times out, that's usually indicative of either a system problem (an MPI or file system problem) or possibly a model problem. 
If a system problem is suspected, try to resubmit the job to see if an intermittent problem occurred. 
Also send help to local site consultants to provide them with feedback about system problems and to get help.

Another error that can cause a timeout is a slow or intermittently slow node. 
The cpl.log file normally outputs the time used for every model simulation day. To review that data, grep the cpl.log file for the string, tStamp
::

   > grep tStamp cpl.log.* | more


which gives output that looks like this::
::

  tStamp_write: model date = 10120 0 wall clock = 2009-09-28 09:10:46 avg dt = 58.58 dt = 58.18
  tStamp_write: model date = 10121 0 wall clock = 2009-09-28 09:12:32 avg dt = 60.10 dt = 105.90


Review the run times for each model day. 
These are indicated at the end of each line. 
The "avg dt = " is the running average time to simulate a model day in the current run and "dt = " is the time needed to simulate the latest model day. 
The model date is printed in YYYYMMDD format and the wall clock is the local date and time. 
So in this case 10120 is Jan 20, 0001, and it took 58 seconds to run that day. 
The next day, Jan 21, took 105.90 seconds. 
If a wide variation in the simulation time is observed for typical mid-month model days, then that is suggestive of a system problem. 
However, be aware that there are variations in the cost of the model over time. 
For instance, on the last day of every simulated month, the model will typically write netcdf files, and this can be a significant intermittent cost. 
Also, some model configurations read data mid- month or run physics intermittently at a timestep longer than one day. 
In those cases, some run time variability would be observed and it would be caused by CESM1, not system variability. 
With system performance variability, the time variation is typically quite erratic and unpredictable.

Sometimes when a job times out, or it overflows disk space, the restart files will get mangled. 
With the exception of the CAM and CLM history files, all the restart files have consistent sizes. 
Compare the restart files against the sizes of a previous restart. 
If they don't match, then remove them and move the previous restart into place before resubmitting the job. 
Please see `restarting a run <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.

On HPC systems, it is not completely uncommon for nodes to fail or for access to large file systems to hang. 
Please make sure a case fails consistently in the same place before filing a bug report.
