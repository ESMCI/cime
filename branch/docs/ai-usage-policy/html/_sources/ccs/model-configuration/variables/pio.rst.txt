.. _model_config_pio:

PIO_SPEC_FILE
=============

.. contents::
    :local:

Overview
--------
Provides CIME with the models PIO configuration.

Entry
-----
The following is an example entry for ``PIO_SPEC_FILE`` in ``config_files.xml``.

Only a single value is required.

.. code-block:: xml

    <entry id="PIO_SPEC_FILE">
        <type>char</type>
        <default_value>$SRCROOT/cime_config/machines/config_pio.xml</default_value>
        <group>case_last</group>
        <file>env_case.xml</file>
        <desc>file containing specification of pio settings for target model possible machine, compiler, mpilib, compset and/or grid attributes (for documentation only - DO NOT EDIT)</desc>
    </entry>

Contents
----------

Schema Definition
`````````````````
Use the `entry` element to describe configuration. This will be dependent on the models PIO configuration. See the following example.

.. code-block:: xml

    <config_pio version="1.0">
        <entry id="PIO_VERSION">
            <values>
                <value>2</value>
            </values>
        </entry>

        <entry id="PIO_STRIDE">
            <values>
                <value>$MAX_MPITASKS_PER_NODE</value>
            </values>
        </entry>

        <entry id="PIO_ROOT">
            <values>
                <value>0</value>
            </values>
        </entry>

        <entry id="PIO_TYPENAME">
            <values>
                <value>pnetcdf</value>
                <value mpilib="mpi-serial">netcdf</value>
                <value mach="userdefined">netcdf</value>
                <value mach="melvin">netcdf</value>
                <value mach="mappy">netcdf</value>
                <value mach="weaver">netcdf</value>
                <value mach="eastwind">netcdf</value>
                <value mach="constance">netcdf</value>
                <value mach="cascade">netcdf</value>
                <value mach="sooty">netcdf</value>
                <value mach="pleiades.*">netcdf</value>
                <value mach="hobart" compiler="pgi">netcdf</value>
                <value mach="oic5">netcdf</value>
                <value mach="lawrencium-lr3">netcdf</value>
                <value mach="lawrencium-lr6">netcdf</value>
                <value mach="eddi">netcdf</value>
                <value mach="cades">netcdf</value>
                <value mach="chicoma-cpu">netcdf</value>
                <value mach="chicoma-gpu">netcdf</value>
                <value mach="bebop" mpilib="impi" compset=".*CAM5.+MPAS.*">netcdf</value>
                <value mach="fugaku" compiler="gnu">netcdf</value>
            </values>
        </entry>

        ...
    </config_pio>