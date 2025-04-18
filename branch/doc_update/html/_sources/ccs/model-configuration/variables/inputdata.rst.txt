.. _model_config_inputdata:

INPUTDATA_SPEC_FILE
===================

.. contents::
    :local:

Entry
-----
The following is an example entry for ``INPUTDATA_SPEC_FILE`` in ``config_files.xml``.

Only a single value is required.

.. code-block:: xml

    <entry id="INPUTDATA_SPEC_FILE">
        <type>char</type>
        <default_value>$SRCROOT/cime_config/config_inputdata.xml</default_value>
        <group>case_last</group>
        <file>env_case.xml</file>
        <desc>file containing inputdata server descriptions  (for documentation only - DO NOT EDIT)</desc>
        <schema>$CIMEROOT/CIME/data/config/xml_schemas/config_inputdata.xsd</schema>
    </entry>    

Contents
--------

Schema Definition
-----------------        

==================  =========================================================================================
Element/Attribute   Description
==================  =========================================================================================
server              Describes an input data server.
comment             Server comment.
protocol            Protocol used to connect to server. Possible values svn, gftp, ftp or wget.
address             Address for the server.
user                Username if required to connect to the server.
password            Password if required to connect to the server.
checksum            Remote path to the checksum file.
inventory           A CSV file containing a list of available data files and the valid date for each.
                    Format should be `pathtofile,YYYY-MM-DD HH:MM:SS`.
ic_filepath         Remote path for initial condition files. 
==================  =========================================================================================

.. code-block:: xml

    <!-- Generated with doc/generate_xmlschema.py CIME/data/config/xml_schemas/config_inputdata.xsd inputdata on 2025-02-06 -->

    <!-- Occurences min: 1 max: 1-->
    <inputdata>
            <!-- Occurences min: 0 max: Unlimited-->
            <server>
                    <!-- Occurences min: 0 max: 1-->
                    <comment></comment>
                    <!-- Occurences min: 1 max: 1-->
                    <protocol></protocol>
                    <!-- Occurences min: 1 max: 1-->
                    <address></address>
                    <!-- Occurences min: 0 max: 1-->
                    <user></user>
                    <!-- Occurences min: 0 max: 1-->
                    <password></password>
                    <!-- Occurences min: 0 max: 1-->
                    <checksum></checksum>
                    <!-- Occurences min: 0 max: 1-->
                    <inventory></inventory>
                    <!-- Occurences min: 0 max: 1-->
                    <ic_filepath></ic_filepath>
            </server>
    </inputdata>