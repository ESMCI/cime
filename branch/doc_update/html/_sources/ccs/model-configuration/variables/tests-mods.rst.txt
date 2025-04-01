.. _model_config_tests_mods:

TESTS_MODS_DIR
==============

.. contents::
    :local:

Provides CIME with the root directories to discover ``TestMods``.

Entry
-----

This is an example entry for ``config_files.xml``.

If the ``component`` attribute is provided then those ``TestMods`` are only available for that component if present in the ``compset``.

.. code-block:: xml

    <entry id="TESTS_MODS_DIR">
        <type>char</type>
        <default_value>unset</default_value>
        <values>
            <value component="allactive">$SRCROOT/cime_config/testmods_dirs</value>
            <value component="drv"      >$COMP_ROOT_DIR_CPL/cime_config/testdefs/testmods_dirs</value>
            <value component="eam"      >$COMP_ROOT_DIR_ATM/cime_config/testdefs/testmods_dirs</value>
            <value component="elm"      >$COMP_ROOT_DIR_LND/cime_config/testdefs/testmods_dirs</value>
            <value component="cice"     >$COMP_ROOT_DIR_ICE/cime_config/testdefs/testmods_dirs</value>
            <value component="mosart"   >$COMP_ROOT_DIR_ROF/cime_config/testdefs/testmods_dirs</value>
            <value component="scream"   >$COMP_ROOT_DIR_ATM/cime_config/testdefs/testmods_dirs</value>
            <value component="eamxx"    >$COMP_ROOT_DIR_ATM/cime_config/testdefs/testmods_dirs</value>
            <value component="mpaso"    >$COMP_ROOT_DIR_OCN/cime_config/testdefs/testmods_dirs</value>
            <value component="mpassi"   >$COMP_ROOT_DIR_ICE/cime_config/testdefs/testmods_dirs</value>
            <value component="ww3"      >$COMP_ROOT_DIR_WAV/cime_config/testdefs/testmods_dirs</value>
            <value component="mali"      >$COMP_ROOT_DIR_GLC/cime_config/testdefs/testmods_dirs</value>
        </values>
        <group>case_last</group>
        <file>env_case.xml</file>
        <desc>directory containing test modifications for primary component tests (for documentation only - DO NOT EDIT)</desc>
    </entry>