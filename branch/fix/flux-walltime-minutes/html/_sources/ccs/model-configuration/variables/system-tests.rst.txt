.. _model_config_system_tests:

SYSTEM_TESTS_DIR
================

.. contents::
    :local:

Overview
--------
Provides CIME with the root directories to discover ``SystemTests``.

Entry
-----
The following is an example entry for ``SYSTEM_TESTS_DIR`` in ``config_files.xml``.

This provides the location for :ref:`SystemTests<system_tests>` for all components.

Additional ``value`` elements are use to add ``SystemTests`` for specific components.

.. code-block:: xml

    <entry id="SYSTEM_TESTS_DIR">
        <type>char</type>
        <values>
            <value component="any">$CIMEROOT/CIME/SystemTests</value>
            <value component="mpaso">$COMP_ROOT_DIR_OCN/cime_config/SystemTests</value>
        </values>
        <group>test</group>
        <file>env_test.xml</file>
        <desc>directories containing cime compatible system test modules</desc>
    </entry>