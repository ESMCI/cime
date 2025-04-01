.. _model_config_batch:

BATCH_SPEC_FILE
===============

.. contents::
    :local:

Entry
-----
The following is an example entry for ``BATCH_SPEC_FILE`` in ``config_files.xml``.

This varaible only requires a single value.

Example
:::::::
.. code-block:: xml

    <entry id="BATCH_SPEC_FILE">
        <type>char</type>
        <default_value>$SRCROOT/cime_config/machines/config_batch.xml</default_value>
        <group>case_last</group>
        <file>env_case.xml</file>
        <desc>File containing batch system details for target system (for documentation only - DO NOT EDIT)</desc>
        <schema>$CIMEROOT/CIME/data/config/xml_schemas/config_batch.xsd</schema>
    </entry>

Contents
--------
The following describes the contents of the ``config_batch.xml`` file.

The **config_batch.xml** schema is defined in **$CIMEROOT/config/xml_schemas/config_batch.xsd**.

CIME supports these batch systems: pbs, cobalt, lsf, and slurm.

The entries in **config_batch.xml** are hierarchical.

#. General configurations for each system are provided at the top of the file.

#. Specific modifications for a given machine are provided below. In particular, each machine should define its own queues.

#. Following is a machine-specific queue section. This section details the parameters for each queue on the target machine.

#. The last section describes several things:

   - Each job that will be submitted to the queue for a CIME workflow,
   - The template file that will be used to generate that job,
   - The prerequisites that must be met before the job is submitted, and
   - The dependencies that must be satisfied before the job is run.

By default, the CIME workflow consists of two jobs (**case.run**, **case.st_archive**).

In addition, there is a **case.test** job that is used by the CIME system test workflow.

Schema Definition
-----------------

.. warning::

    Under ``submit_args`` the ``arg`` element is deprecated in favor of ``argument``.

.. code-block:: xml

    <!-- Generated with doc/generate_xmlschema.py CIME/data/config/xml_schemas/config_batch.xsd config_batch on 2025-02-06 -->

    <!-- Attributes 'version' is required-->
    <!-- Occurrences min: 1 max: 1-->
    <config_batch version="">
        <!-- Attributes 'MACH' is optional,'type' is required,'version' is optional-->
        <!-- Occurrences min: 1 max: Unlimited-->
        <batch_system MACH="" type="" version="">
            <!-- Attributes 'args' is optional,'per_job_arg' is optional-->
            <!-- Occurrences min: 0 max: 1-->
            <batch_query args="" per_job_arg="">
            </batch_query>
            <!-- Occurrences min: 0 max: 1-->
            <batch_submit></batch_submit>
            <!-- Occurrences min: 0 max: 1-->
            <batch_cancel></batch_cancel>
            <!-- Occurrences min: 0 max: 1-->
            <batch_redirect></batch_redirect>
            <!-- Occurrences min: 0 max: 1-->
            <batch_env></batch_env>
            <!-- Occurrences min: 0 max: 1-->
            <batch_directive></batch_directive>
            <!-- Occurrences min: 0 max: 1-->
            <jobid_pattern></jobid_pattern>
            <!-- Occurrences min: 0 max: 1-->
            <depend_string></depend_string>
            <!-- Occurrences min: 0 max: 1-->
            <depend_allow_string></depend_allow_string>
            <!-- Occurrences min: 0 max: 1-->
            <depend_separator></depend_separator>
            <!-- Occurrences min: 0 max: 1-->
            <walltime_format></walltime_format>
            <!-- Occurrences min: 0 max: 1-->
            <batch_mail_flag></batch_mail_flag>
            <!-- Occurrences min: 0 max: 1-->
            <batch_mail_type_flag></batch_mail_type_flag>
            <!-- Occurrences min: 0 max: 1-->
            <batch_mail_type></batch_mail_type>
            <!-- Occurrences min: 0 max: 1-->
            <batch_mail_default></batch_mail_default>
            <!-- Occurrences min: 0 max: 1-->
            <submit_args>
                <!-- Attributes 'flag' is required,'name' is optional-->
                <!-- Occurrences min: 1 max: Unlimited-->
                <arg flag="" name="">
                </arg>
                <!-- Attributes 'job_queue' is optional-->
                <!-- Occurrences min: 1 max: Unlimited-->
                <argument job_queue="">
                </argument>
            </submit_args>
            <!-- Attributes 'None' is None-->
            <!-- Occurrences min: 0 max: Unlimited-->
            <directives None="">
                <!-- Attributes 'default' is optional,'prefix' is optional-->
                <!-- Occurrences min: 1 max: Unlimited-->
                <directive default="" prefix="">
                </directive>
            </directives>
            <!-- Occurrences min: 0 max: 1-->
            <unknown_queue_directives></unknown_queue_directives>
            <!-- Occurrences min: 0 max: 1-->
            <queues>
                <!-- Attributes 'default' is optional,'strict' is optional,'nodemax' is optional,'nodemin' is optional,'jobmax' is optional,'jobmin' is optional,'jobname' is optional,'walltimemax' is optional,'walltimemin' is optional,'walltimedef' is optional-->
                <!-- Occurrences min: 1 max: Unlimited-->
                <queue default="" strict="" nodemax="" nodemin="" jobmax="" jobmin="" jobname="" walltimemax="" walltimemin="" walltimedef=""></queue>
            </queues>
        </batch_system>
        <!-- Occurrences min: 0 max: 1-->
        <batch_jobs>
            <!-- Attributes 'name' is required-->
            <!-- Occurrences min: 1 max: Unlimited-->
            <job name="">
                <!-- Occurrences min: 1 max: 1-->
                <template></template>
                <!-- Occurrences min: 0 max: 1-->
                <task_count></task_count>
                <!-- Occurrences min: 0 max: 1-->
                <walltime></walltime>
                <!-- Occurrences min: 0 max: 1-->
                <dependency></dependency>
                <!-- Occurrences min: 1 max: 1-->
                <prereq></prereq>
            </job>
        </batch_jobs>
    </config_batch>