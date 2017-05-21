.. _setting-up-a-case:

*********************************
Setting up a Case
*********************************

===================================
Calling **case.setup**
===================================

After creating a case or changing aspects of the case such as the pe-layout, you need to call the **case.setup** command from ``$CASEROOT``. 
To see the options to **case.setup** use the ``--help`` option. 

Calling ``case.setup`` creates the following **additional** files and directories in ``$CASEROOT``: 

   =============================   ===============================================================================================================================
   case.run                        Run script containing the batch directives 

                                   The batch directives are generated using the contents of env_mach_pes.xml.
				   Calling **case.setup --clean** will remove this file.

   Macros.make		           File containing machine-specific makefile directives for your target platform/compiler. 

                                   This file is only created if it does not already exist in the case is called. 

				   This file can be modified by the user to change certain aspects of the build such as compiler flags.

				   Calling **case.setup -clean** will not remove the Macros.make file once it has been created.  
				   However if you remove or rename the Macros.make file case.setup will recreate it for you.

   user_nl_xxx[_NNNN] files	   Files where all user modifications to component namelists are made. 

                                   xxx denotes any one of the set of components targeted for the specific case 

                                   For example, for a full active CESM compset, xxx would denote [cam,clm,rtm,cice,pop2,cism2,ww3,cpl] 

                                   NNNN goes from 0001 to the number of instances of that component (see :ref:`multiple instances<multi-instance>`)

	                           For a case with 1 instance of each component (default), NNNN will not appear in the user_nl file names. 

                                   A user_nl file of a given name will only be created once. 

                                   Calling **case.setup -clean** will *not remove* any user_nl files. 

				   Changing the number of instances in the ``env_mach_pes.xml`` will only cause new user_nl files to be added to ``$CASEROOT``.
   CaseDocs/			   Directory that contains all the component namelists for the run. 

                                   This is for reference only and files in this directory SHOULD NOT BE EDITED since they will 
                                   be overwritten at build time and run time. 

   .env_mach_specific.[cs,sh]      Files summarizing the module load commands and environment variables that are set when the scripts in ``$CASEROOT`` are called. 
	                           These files are not used by the case but can be useful for debugging case module load and environment settings.

   software_environment.txt	   This file records some aspects of the computing system the case is built on, such as the shell environment.
   =============================   ===============================================================================================================================



