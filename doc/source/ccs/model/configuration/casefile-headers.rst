.. _model_config_casefile_headers:

Case File Headers 
================

.. contents::
    :local:

Provides CIME with all the ``env_*`` files that should be created and stored in a case.

Entry
-----

This is an example entry for ``config_files.xml``.

.. code-block:: xml
    :tab-width: 4

    <entry id="CASEFILE_HEADERS">
        <type>char</type>
        <default_value>$CIMEROOT/CIME/data/config/config_headers.xml</default_value>
        <group>case_der</group>
        <file>env_case.xml</file>
        <desc>contains both header and group information for all the case env_*.xml files </desc>
    </entry>


Definition
-------------

.. warning::

    It's best to use the ``config_headers.xml`` in the CIME repository has CIME expects certain ``env_*.xml`` files to be present in a case.

Schema
```````

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
