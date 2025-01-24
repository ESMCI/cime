.. _adding-component-cime:

Adding a New Component Model to CIME
====================================

Overview
--------

CIME’s modular design allows for seamless integration of new component models into its infrastructure. To add a new component model, you must ensure compatibility with CIME’s interfaces and follow the defined setup for component registration, coupling, and testing.

This guide covers the essential steps to integrate a new component model into CIME.

---

Prerequisites
-------------

- Familiarity with the CIME framework and component model architecture.
- A working implementation of the new component model, including its source code, build scripts, and runtime configuration files.
- Access to the CIME source code repository.

---

Steps to Add a New Component Model
----------------------------------

1. Directory Structure
~~~~~~~~~~~~~~~~~~~~~

Each component model requires a dedicated directory under the ``components/`` directory in the CIME source tree. Follow these steps:

1. **Create the Directory:**

   .. code-block:: bash

      mkdir components/<model_name>

2. **Add Source Code:**
   Place the source code, configuration files, and necessary scripts for the new model into the directory.

3. **Follow Naming Conventions:**
   Although not required, it is recommended to use consistent naming conventions for directory names and files. It is also conventional to define a subdirectory ``cime_config`` within the component directory. This subdirectory contains all files linking CIME to the component model. Three files are required:

   - **``config_component.xml``:** Describes the component and its input options.
   - **``buildlib``:** A Python script providing the interface to build the model.
   - **``buildnml``:** A Python script to stage the component's inputs.

   Additionally, other optional interface files may be provided in ``cime_config`` to support advanced functionality:

   - **``config_archive.xml``:** Defines archiving rules for model outputs.
   - **``config_compsets.xml``:** Defines compsets specific to the component.
   - **``config_tests.xml``:** Describes test configurations.
   - **``config_pes.xml``:** Specifies processor layout and scaling.

   If the component includes system tests, it is conventional to add a subdirectory, typically named ``SystemTests``, to house these tests. This name is configurable via ``config_files.xml``.

   Example structure:

   .. code-block:: text

      components/<model_name>/
      ├── src/         # Source code
      ├── build/       # Build scripts
      ├── cime_config/ # CIME interface files
      │   ├── config_component.xml
      │   ├── buildlib
      │   ├── buildnml
      │   ├── config_archive.xml (optional)
      │   ├── config_compsets.xml (optional)
      │   ├── config_tests.xml (optional)
      │   └── config_pes.xml (optional)
      ├── SystemTests/ # System tests (optional)
      └── README.md    # Documentation for the component

---

2. Configure the Component Interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CIME requires each component model to adhere to a standard interface for communication with the coupler. Implement the following:

1. **Component-Specific Interface File:** Each component is required to have a file named <class>_comp_<driver>.F90, where <class> specifies the component type (e.g., atm, lnd, ice, rof, glc, wav, cpl, esp) and driver specifies the model driver (nuopc or mct). For nuopc this file must define a public routine SetServices that sets pointers to the model's phase routines, for mct the phase routine names (initialize, run, and finalize) are assumed and must be present.

CESM uses the NUOPC (National Unified Operational Prediction Capability) system as the underlying framework for component interaction. For detailed guidance on implementing and configuring the NUOPC-based interfaces, refer to the NUOPC Layer Documentation <https://www.earthsystemcog.org/projects/nuopc>_.

E3SM uses the MCT (Model Coupling Toolkit) system as the framework.   Detailed guidance on implementing and configuring the MCT-based interfaces can be found in <https://www.mcs.anl.gov/research/projects/mct/mct_APIs.pdf>_.

2. **Initialize the Component:**
   Include an initialization routine (``<model_name>_init``) that defines initial conditions and grid mappings.

3. **Run and Finalize Routines:**
   Ensure the model includes ``run`` and ``finalize`` routines to handle time-stepping and cleanup.

4. **Data Exchange:**
   Define the variables exchanged with the coupler (e.g., fluxes, states) in the component's ``nuopc`` or ``drv`` directory.

---

3. Register the Component
~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Define Component Root Directory:**
   Each component model must define its root directory using the variable ``COMP_ROOT_DIR_XXX`` in the ``config_files.xml`` file, where ``XXX`` represents the component class (e.g., ATM, LND, ICE). For example:

   .. code-block:: xml

      <entry id="COMP_ROOT_DIR_ATM">
    <type>char</type>
    <values>
      <value component="datm"  >$SRCROOT/components/cdeps/datm</value>
      <value component="satm"  >$CIMEROOT/CIME/non_py/src/components/stub_comps_$COMP_INTERFACE/satm</value>
      <value component="xatm"  >$CIMEROOT/CIME/non_py/src/components/xcpl_comps_$COMP_INTERFACE/xatm</value>

      <value component="cam"                         >$SRCROOT/components/cam/</value>
      <value component="ufsatm"                      >$SRCROOT/components/fv3/</value>
      <value component="myatm"                      >$SRCROOT/components/myatm/</value>
    </values>
    <group>case_comps</group>
    <file>env_case.xml</file>
    <desc>Root directory of the case atmospheric component  </desc>
    <schema>$CIMEROOT/CIME/data/config/xml_schemas/config_compsets.xsd</schema>
  </entry>

2. **Update ``config_compsets.xml``:**
   The ``config_compsets.xml`` file can be used to define aliases for long compset names, easing the burden of specifying full names. However, aliases are optional. 

   The component name in the long compset name must match the name used in the ``description`` section of the ``config_component.xml`` file. Additionally, the ``config_component.xml`` file must include a variable ``COMP_XXX`` (where ``XXX`` is the component class, e.g., ATM, LND, ICE). This variable is essential for defining the component in the context of CIME.

---

4. Modify the Coupler Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Edit ``cime_config/config_files.xml``:**
   Add entries specifying how the new component interfaces with the coupler.

2. **Define Flux Mappings:**
   Ensure fluxes exchanged between the new model and other components (e.g., atmosphere, land, ocean) are well-defined.

3. **Grid Compatibility:**
   Verify the model supports the necessary grid resolutions and that mappings are registered.

---

5. Test the Integration
~~~~~~~~~~~~~~~~~~~~~~

1. **Create Test Cases:**
   Write test cases in the ``tests/`` directory to validate the integration of the new component.

2. **Run Validation Tests:**
   Use CIME’s testing framework to ensure the new component functions correctly:

   .. code-block:: bash

      ./create_test --xml-testlist-file <test_list.xml>

3. **Debug Errors:**
   Review log files in the ``CaseDocs`` and ``Logs`` directories for issues.

---

6. Document the New Component
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Write Documentation:**
   Provide a README file in the ``components/<model_name>/`` directory describing:

   - The component's purpose.
   - Input and output data requirements.
   - Build and runtime instructions.

2. **Update Central Documentation:**
   Add details about the new component to CIME’s central documentation files.

---

7. Submit Changes
~~~~~~~~~~~~~~~~~

1. **Commit the Changes:**

   .. code-block:: bash

      git add components/<model_name>
      git commit -m "Add new component model: <model_name>"

2. **Submit a Pull Request:**
   Push the changes to the CIME repository and submit a pull request for review.

---

Example
-------

Adding a New Land Model (``MyLandModel``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Create ``components/mylandmodel/`` with the required directory structure.
2. Implement the interface routines (``mylandmodel_init``, ``mylandmodel_run``, ``mylandmodel_finalize``).
3. Define the component's root directory in ``config_files.xml`` using the variable ``COMP_ROOT_DIR_LND``.
4. Register ``MyLandModel`` in ``config_compsets.xml``.
5. Define flux mappings in the coupler configuration files.
6. Test the integration using predefined compsets and submit results for validation.

