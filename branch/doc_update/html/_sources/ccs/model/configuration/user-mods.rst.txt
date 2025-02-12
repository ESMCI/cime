.. _model_config_user_mods:

User Mods
=============

.. contents::
    :local:

Provides CIME with the root directories to discover ``UserMods``.

Entry
-----

This is an example entry for ``config_files.xml``.

Each ``value`` element points to directory to find component specific ``UserMods``.

.. code-block:: xml

    <entry id="USER_MODS_DIR">
        <type>char</type>
        <default_value>unset</default_value>
        <values>
        <value component="allactive">$SRCROOT/cime_config/usermods_dirs</value>
        <value component="drv"      >$COMP_ROOT_DIR_CPL/cime_config/usermods_dirs</value>
        <value component="eam"      >$COMP_ROOT_DIR_ATM/cime_config/usermods_dirs</value>
        <value component="elm"      >$COMP_ROOT_DIR_LND/cime_config/usermods_dirs</value>
        <value component="cice"     >$COMP_ROOT_DIR_ICE/cime_config/usermods_dirs</value>
        <value component="mosart"   >$COMP_ROOT_DIR_ROF/cime_config/usermods_dirs</value>
        <value component="scream"   >$COMP_ROOT_DIR_ATM/cime_config/usermods_dirs</value>
        </values>
        <group>case_last</group>
        <file>env_case.xml</file>
        <desc>directory containing user modifications for primary components (for documentation only - DO NOT EDIT)</desc>
    </entry>