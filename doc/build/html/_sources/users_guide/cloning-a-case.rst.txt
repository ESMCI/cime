.. _cloning-a-case:

**************************
Cloning a Case
**************************

If you have access to the run you want to clone, the **create_clone** command will create a new case while also preserving local modifications to the case that you want to clone.
You can run the utility **create_clone** from the cime/scripts directory.
It has the following arguments:

--case

  The name or path of the new case.

--clone

  The full pathname of the case to be cloned.

--cime-output-root

  The root path below which the case run and bld directories will be created.  You should use this option if you are cloning a case owned by
  another user.

--keepexe

  Sets **$EXEROOT** to point to the original case.

--project

  Specify a project code for the new case.

--mach-dir

  Specify an alternate location of the machines directory.

--silent

  Enables silent mode. Only fatal messages will be issued.

--verbose

  Echoes all settings.

--debug

  Print very verbose debug information to the file **create_clone.log**

--help

  Prints usage instructions.

Here is the simplest example of using **create_clone**:
::

   > cd $CIMEROOT/scripts
   > create_clone --case $CASEROOT --clone $CLONEROOT

**create_clone** will preserve any local namelist modifications made in the user_nl_xxxx files as well as any source code modifications in the SourceMods tree.

**Important**:: Do not change anything in the ``env_case.xml`` file.
The ``$CASEROOT/`` directory will now appear as if **create_newcase** had just been run -- with the exception that local modifications to the env_* files are preserved.

Another approach to duplicating a case is to use the information in that case's ``README.case`` and ``CaseStatus`` files to create a new case and duplicate the relevant ``xlmchange`` commands that were issued in the original case.
Note that this alternative will *not* preserve any local modifications that were made to the original case, such as source-code or build-script modifications; you will need to import those changes manually.
