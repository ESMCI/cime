.. _model_config_tests_spec:

TESTS_SPEC_FILE
===============

.. contents::
    :local:

Overview
--------

.. warning::

    This is an untested feature.

Provides configuration refinement for machines. Can be used to specify machine specific configuration.

Entry
-----

This is an example entry for ``config_files.xml``.

.. code-block:: xml

    <entry id="TESTS_SPEC_FILE">
        <type>char</type>
        <default_value>unset</default_value>
        <group>case_last</group>
        <file>env_case.xml</file>
        <desc>file containing specification of all system tests for primary component (for documentation only - DO NOT EDIT)</desc>
    </entry>