.. _model_config_tests:

CONFIG_TESTS_FILE
=================

.. contents::
    :local:

Provides CIME with defaults for various ``SystemTests``.

Entry
-----

This is an example entry for ``config_files.xml``.

If the ``component`` attribute is provided then it will only apply to ``SystemTests`` discovered for that component.

.. code-block:: xml

    <entry id="CONFIG_TESTS_FILE">
        <type>char</type>
        <values>
            <value>$CIMEROOT/CIME/data/config/config_tests.xml</value>
            <value component="mpaso">$COMP_ROOT_DIR_OCN/cime_config/config_tests.xml</value>
        </values>
        <group>test</group>
        <file>env_test.xml</file>
        <desc>file containing system test descriptions </desc>
    </entry>

Definition Schema
-----------------
This is an example of the default configuration for the ``ERI`` system test.

=================== ===========================================================================================
Element/Attribute   Description
=================== ===========================================================================================
test                Define a test configuration.
NAME                Name of the test.
DESC                Description of the test.
INFO_DBUG           Coupler log verbosity.
STOP_OPTION         The stop option, possible values nyears, nmonths, ndays, nhours, nseconds, nsteps.
STOP_N              Length of run.
DOUT_S              Whether to archive.
RUN_TYPE            The type of run the test uses.
RUN_REFCASE         Name of the reference case.
RUN_REFDATE         Date to start branch/hybrid case from.
RUN_REFTOD          Time to start branch/hybrid case from.
REST_OPTION         The restart option, possible values nyears, nmonths, ndays, nhours, nseconds, nsetps.
REST_N              Length between each restart file written.
GET_REFCASE         Whether a reference case is used to pre-stage data.
CONTINUE_RUN        Whether a run should continue after resubmitting.
HIST_OPTION         The history option, possible values nyears, nmonths, ndays, nhours, nseconds, nsetps.
HIST_N              Length between each history file written.
=================== ===========================================================================================

.. code-block:: xml

    <config_test>
            <test NAME="ERI">
                    <DESC>hybrid/branch/exact restart test, default 3+19/10+9/5+4 days</DESC>
                    <INFO_DBUG>1</INFO_DBUG>
                    <STOP_OPTION>ndays</STOP_OPTION>
                    <STOP_N>22</STOP_N>
                    <DOUT_S>FALSE</DOUT_S>
                    <RUN_TYPE>startup</RUN_TYPE>
                    <RUN_REFCASE>case.std</RUN_REFCASE>
                    <RUN_REFDATE>0001-01-01</RUN_REFDATE>
                    <RUN_REFTOD>00000</RUN_REFTOD>
                    <REST_OPTION>ndays</REST_OPTION>
                    <REST_N>$STOP_N</REST_N>
                    <GET_REFCASE>FALSE</GET_REFCASE>
                    <CONTINUE_RUN>FALSE</CONTINUE_RUN>
                    <HIST_OPTION>never</HIST_OPTION>
                    <HIST_N>-999</HIST_N>
            </test>
    </config_test>