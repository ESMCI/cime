.. _model_config_casefile_headers:

CASEFILE_HEADERS
================

.. contents::
    :local:

Entry
-----
The following is an example entry for ``CASEFILE_HEADERS`` in ``config_files.xml``.

Only a single value is required.

.. code-block:: xml
    :tab-width: 4

    <entry id="CASEFILE_HEADERS">
        <type>char</type>
        <default_value>$CIMEROOT/CIME/data/config/config_headers.xml</default_value>
        <group>case_der</group>
        <file>env_case.xml</file>
        <desc>contains both header and group information for all the case env_*.xml files </desc>
    </entry>


Contents
--------

.. warning::

    It's best to use the ``config_headers.xml`` in the CIME repository has CIME expects certain ``env_*.xml`` files to be present in a case.

Schema Definition
-----------------

.. code-block:: xml
    :tab-width: 4

    <files>
        <file name="env_batch.xml">
            <header>
            These variables may be changed anytime during a run, they
            control arguments to the batch submit command.
            </header>
        </file>
    </files>
