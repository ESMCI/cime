.. _model_config_cmake_macros_dir:

CMAKE_MACROS_DIR
================

.. contents::
    :local:

Entry
-----
The following is an example for ``CMAKE_MACROS_DIR`` in ``config_files.xml``.

This variable is used to set the directory where the cmake macros are located. This is a required variable for the build system.

.. code-block:: xml

    <entry id="CMAKE_MACROS_DIR">
        <type>char</type>
        <default_value>$SRCROOT/cime_config/machines/cmake_macros</default_value>
        <group>case_last</group>
        <file>env_case.xml</file>
        <desc>Directory containing cmake macros (for documentation only - DO NOT EDIT)</desc>
    </entry>

.. _model_config_cmake_macros_dir_def:
Configuration
-------------

This is a directory containing machine/compiler cmake macros that will be loaded during the build process.

To make these macro files available to the build system you'll need two files; ``CMakeLists.txt`` and ``Macros.cmake``.

Naming convention
`````````````````

The cmake macro files will be loaded using this hiearchy with more specific files taking precedence.

- universal.cmake
- <compiler>.cmake
- <mach>.cmake
- <compiler>_<mach>.cmake

Required Files
``````````````
These files will be copied to the ``CASEROOT/cmake_macros`` directory and used to load the appropriate macro files for the machine.

CMakeLists.txt
::::::::::::::

.. code-block:: cmake

    cmake_policy(SET CMP0057 NEW)
    cmake_minimum_required(VERSION 3.5)
    project(cime LANGUAGES C Fortran)
    include(${CMAKE_CURRENT_BINARY_DIR}/../Macros.cmake)

Macros.cmake
::::::::::::

.. code-block:: cmake

    cmake_policy(SET CMP0057 NEW)

    set(MACROS_DIR ${CASEROOT}/cmake_macros)

    set(UNIVERSAL_MACRO ${MACROS_DIR}/universal.cmake)
    set(COMPILER_MACRO ${MACROS_DIR}/${COMPILER}.cmake)
    set(MACHINE_MACRO ${MACROS_DIR}/${MACH}.cmake)
    set(COMPILER_MACHINE_MACRO ${MACROS_DIR}/${COMPILER}_${MACH}.cmake)
    set(POST_PROCESS_MACRO ${SRCROOT}/cime_config/machines/cmake_macros/post_process.cmake)

    if (CONVERT_TO_MAKE)
        get_cmake_property(E3SM_CMAKE_INTERNAL_VARS_BEFORE_BUILD_INTERNAL_IGNORE VARIABLES)
        foreach (VAR_BEFORE IN LISTS E3SM_CMAKE_INTERNAL_VARS_BEFORE_BUILD_INTERNAL_IGNORE)
            set("E3SM_CMAKE_INTERNAL_${VAR_BEFORE}" "${${VAR_BEFORE}}")
        endforeach()
        list(APPEND E3SM_CMAKE_INTERNAL_VARS_BEFORE_BUILD_INTERNAL_IGNORE "VAR_BEFORE")
        list(APPEND E3SM_CMAKE_INTERNAL_VARS_BEFORE_BUILD_INTERNAL_IGNORE "MACRO_FILE")
    endif()

    # Include order defines precedence
    foreach (MACRO_FILE ${UNIVERSAL_MACRO} ${COMPILER_MACRO} ${MACHINE_MACRO} ${COMPILER_MACHINE_MACRO} ${POST_PROCESS_MACRO})
        if (EXISTS ${MACRO_FILE})
            include(${MACRO_FILE})
        else()
            message("No macro file found: ${MACRO_FILE}")
        endif()
    endforeach()

    if (CONVERT_TO_MAKE)
        get_cmake_property(VARS_AFTER VARIABLES)

        foreach (VAR_AFTER IN LISTS VARS_AFTER)
            if (VAR_AFTER MATCHES "^E3SM_CMAKE_INTERNAL_")
                # skip
            else()
                if (NOT VAR_AFTER IN_LIST E3SM_CMAKE_INTERNAL_VARS_BEFORE_BUILD_INTERNAL_IGNORE)
                    message("CIME_SET_MAKEFILE_VAR ${VAR_AFTER} := ${${VAR_AFTER}}")
                    list(APPEND E3SM_CMAKE_INTERNAL_VARS_BEFORE_BUILD_INTERNAL_IGNORE "${VAR_AFTER}")
                    set("E3SM_CMAKE_INTERNAL_${VAR_AFTER}" "${${VAR_AFTER}}")
                elseif (NOT "${${VAR_AFTER}}" STREQUAL "${E3SM_CMAKE_INTERNAL_${VAR_AFTER}}")
                    message("CIME_SET_MAKEFILE_VAR ${VAR_AFTER} := ${${VAR_AFTER}}")
                    set("E3SM_CMAKE_INTERNAL_${VAR_AFTER}" "${${VAR_AFTER}}")
                endif()
            endif()
        endforeach()
    endif()

Directory Structure
-------------------

.. code-block::

    cmake_macros
        CMakeList.txt
        Macros.cmake
        ...
