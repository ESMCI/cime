.. _model_config_workflow:

WORKFLOW_SPEC_FILE
==================

.. contents::
   :local:

Overview
--------
Provides CIME with a models various ``workflows``.

Entry
-----

This is an example entry for ``config_files.xml``.

.. code-block:: xml

   <entry id="WORKFLOW_SPEC_FILE">
      <type>char</type>
      <default_value>$SRCROOT/cime_config/machines/config_workflow.xml</default_value>
      <group>case_last</group>
      <file>env_case.xml</file>
      <desc>file containing workflow (for documentation only - DO NOT EDIT)</desc>
      <schema>$CIMEROOT/CIME/data/config/xml_schemas/config_workflow.xsd</schema>
   </entry>

Schema Definition
-----------------

======================= ==================================
Element/Attributes      Description
======================= ==================================
workflow_jobs           Describe jobs in a workflow.
id                      Workflow identifier.
prepend                 Workflow to prepend to current workflow.
append                  Workflow to append to current workflow.
job                     Describe the job.
name                    Name of the job.
template                Template file for job submission.
hidden                  
queue                   Optional queue name for batch submission (at job level).
dependency              Job dependencies.
prereq                  Job pre-requirements.
runtime_parameters      Describe runtime parameters for the job.
MACH                    Which machine these runtime parameters should be used on.
task_count              Task count for the job.
tasks_per_node          Number of tasks per node.
mem_per_task            Memory per task for the job.
walltime                Walltime for the job.
queue                   Optional queue name for batch submission (machine-specific).
======================= ==================================

.. code-block:: xml

    <!-- Generated with doc/generate_xmlschema.py CIME/data/config/xml_schemas/config_workflow.xsd config_workflow on 2025-02-11 -->

    <!-- Attributes 'version' is required-->
    <!-- Occurences min: 1 max: 1-->
    <config_workflow version="">
        <!-- Attributes 'id' is required,'prepend' is optional,'append' is optional-->
        <!-- Occurences min: 1 max: Unlimited-->
        <workflow_jobs id="" prepend="" append="">
            <!-- Attributes 'name' is required-->
            <!-- Occurences min: 1 max: Unlimited-->
            <job name="">
                <!-- Occurences min: 1 max: 1-->
                <template></template>
                <!-- Occurences min: 0 max: 1-->
                <hidden></hidden>
                <!-- Occurences min: 0 max: 1-->
                <queue></queue>
                <!-- Occurences min: 0 max: 1-->
                <dependency></dependency>
                <!-- Occurences min: 1 max: 1-->
                <prereq></prereq>
                <!-- Attributes 'MACH' is optional-->
                <!-- Occurences min: 0 max: Unlimited-->
                <runtime_parameters MACH="">
                    <!-- Occurences min: 0 max: 1-->
                    <task_count></task_count>
                    <!-- Occurences min: 0 max: 1-->
                    <tasks_per_node></tasks_per_node>
                    <!-- Occurences min: 0 max: 1-->
                    <mem_per_task></mem_per_task>
                    <!-- Occurences min: 0 max: 1-->
                    <walltime></walltime>
                    <!-- Occurences min: 0 max: 1-->
                    <queue></queue>
                </runtime_parameters>
            </job>
        </workflow_jobs>
    </config_workflow>

Usage
-----

The ``queue`` element allows you to specify which batch queue should be used for a specific job in the workflow. This is particularly useful for jobs like batched builds that may not require GPU nodes.

**Example:**
To specify a debug queue for the ``case.build`` job while other jobs use their default queues:

.. code-block:: xml

    <workflow_jobs id="default">
        <job name="case.build">
            <template>$CIMEROOT/CIME/Templates/case.build.template</template>
            <prereq>TRUE</prereq>
            <queue>debug</queue>
        </job>
        <job name="case.run">
            <template>$CIMEROOT/CIME/Templates/case.run.template</template>
            <prereq>TRUE</prereq>
        </job>
    </workflow_jobs>

**Machine-specific queues:**
You can also specify different queues for different machines using runtime_parameters:

.. code-block:: xml

    <job name="case.build">
        <template>$CIMEROOT/CIME/Templates/case.build.template</template>
        <prereq>TRUE</prereq>
        <runtime_parameters MACH="machine1">
            <queue>debug</queue>
        </runtime_parameters>
        <runtime_parameters MACH="machine2">
            <queue>short</queue>
        </runtime_parameters>
    </job>

**Notes:**
- The queue specified in the workflow configuration must exist on the target system. If the queue is not available, a warning is logged and the default queue selection is used.
- Queue names vary by machine and batch system (e.g., slurm, PBS, LSF).
- The queue element is optional and defaults to the regular queue selection process if not specified.
