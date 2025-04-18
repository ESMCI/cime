.. _model_config_archive:

ARCHIVE_SPEC_FILE
=================

.. contents::
    :local:

Entry
-----
The following is an example entry for ``ARCHIVE_SPEC_FILE`` in ``config_files.xml``.

Each ``value`` corresponds with the archive configuration for a specific component.

Example
:::::::
.. code-block:: xml

    <entry id="ARCHIVE_SPEC_FILE">
        <type>char</type>
        <values>
            <value>$SRCROOT/cime_config/config_archive.xml</value>
            <value component="drv">$COMP_ROOT_DIR_CPL/cime_config/config_archive.xml</value>
            <!-- data model components -->
            <value component="drof">$COMP_ROOT_DIR_ROF/cime_config/config_archive.xml</value>
            <value component="datm">$COMP_ROOT_DIR_ATM/cime_config/config_archive.xml</value>
            <value component="dice">$COMP_ROOT_DIR_ICE/cime_config/config_archive.xml</value>
            <value component="dlnd">$COMP_ROOT_DIR_LND/cime_config/config_archive.xml</value>
            <value component="docn">$COMP_ROOT_DIR_OCN/cime_config/config_archive.xml</value>
            <value component="dwav">$COMP_ROOT_DIR_WAV/cime_config/config_archive.xml</value>
            <!-- external model components -->
        </values>
        <group>case_last</group>
        <file>env_case.xml</file>
        <desc>file containing specification of archive files for each component (for documentation only - DO NOT EDIT)</desc>
        <schema>$CIMEROOT/CIME/data/config/xml_schemas/config_archive.xsd</schema>
    </entry>

Contents
--------
The following describes the contents of the ``config_archive.xml`` file.

Schema Definition
:::::::::::::::::
Below is the schema definition for the ``config_archive.xml`` file.

=====================   ==============================================================================================
Element/Attribute       Description
=====================   ==============================================================================================
comp_archive_spec       Component archive specification defined for either a specific compnent or class.
compname                Component name the specification applies.
compclass               Component class the specification applies. 
exclude_testing         Whether to exclude the testing archiving.
rest_file_extension     Suffix used to match restart files.
hist_file_extension     Suffix used to match history files.
hist_file_ext_regex     Regular expression used to match file extension of history files.
rest_history_varname    The variable name from restart files used to identify history files required for restarts.
rpointer_file           The rpointer file to create.
rpointer_content        The content that is written to the rpointer file.
tfile                   A filename used to test the component archive specification.
disposition             The expected action to be performed on the file. Possible values copy, move, ignore.
=====================   ==============================================================================================

.. code-block:: xml

    <!-- Generated with doc/generate_xmlschema.py CIME/data/config/xml_schemas/config_archive.xsd components on 2025-02-07 -->

    <!-- Attributes 'version' is optional-->
    <!-- Occurences min: 1 max: 1-->
    <components version="">
            <!-- Attributes 'compname' is required,'compclass' is required,'exclude_testing' is optional-->
            <!-- Occurences min: 0 max: Unlimited-->
            <comp_archive_spec compname="" compclass="" exclude_testing="">
                    <!-- Occurences min: 0 max: Unlimited-->
                    <rest_file_extension></rest_file_extension>
                    <!-- Occurences min: 0 max: Unlimited-->
                    <hist_file_extension></hist_file_extension>
                    <!-- Occurences min: 0 max: Unlimited-->
                    <hist_file_ext_regex></hist_file_ext_regex>
                    <!-- Occurences min: 0 max: Unlimited-->
                    <rest_history_varname></rest_history_varname>
                    <!-- Occurences min: 0 max: Unlimited-->
                    <rpointer>
                            <!-- Occurences min: 0 max: Unlimited-->
                            <rpointer_file></rpointer_file>
                            <!-- Occurences min: 0 max: Unlimited-->
                            <rpointer_content></rpointer_content>
                    </rpointer>
                    <!-- Occurences min: 0 max: 1-->
                    <test_file_names>
                            <!-- Attributes 'disposition' is optional-->
                            <!-- Occurences min: 0 max: Unlimited-->
                            <tfile disposition=""></tfile>
                    </test_file_names>
            </comp_archive_spec>
    </components>