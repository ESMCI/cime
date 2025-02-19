.. _model_config_model:

Model
=====

.. contents::
    :local:

Defines the name of the model for CIME.

Entry
-----

This is an example entry for ``config_files.xml``.

.. code-block:: xml
    
    <entry id="MODEL">
        <type>char</type>
        <default_value>e3sm</default_value>
        <group>case_der</group>
        <file>env_case.xml</file>
        <desc>model system name</desc>
    </entry>
