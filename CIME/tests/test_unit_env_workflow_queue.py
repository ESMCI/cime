#!/usr/bin/env python3

"""
Unit tests for EnvWorkflow queue selection functionality
"""

import os
import tempfile
import unittest

from CIME.XML.env_workflow import EnvWorkflow


class TestEnvWorkflowQueue(unittest.TestCase):
    """Test cases for EnvWorkflow queue functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_files = []

    def tearDown(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def _create_workflow_xml(self, content):
        """Helper to create a temporary env_workflow XML file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(content)
            temp_file = f.name
        self.temp_files.append(temp_file)
        return temp_file

    def test_get_queue_with_queue_entry(self):
        """Test retrieving queue when queue entry exists"""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<env_workflow>
  <group id="case.build">
    <entry id="queue" value="debug">
      <type>char</type>
    </entry>
    <entry id="JOB_QUEUE" value="debug">
      <type>char</type>
    </entry>
  </group>
  <group id="case.run">
    <entry id="JOB_QUEUE" value="">
      <type>char</type>
    </entry>
  </group>
</env_workflow>"""

        temp_file = self._create_workflow_xml(xml)
        workflow = EnvWorkflow(infile=temp_file)

        # Test job with queue
        queue = workflow.get_queue("case.build")
        self.assertEqual(queue, "debug")

        # Test job without queue
        queue = workflow.get_queue("case.run")
        self.assertIsNone(queue)

    def test_get_queue_with_resolved_value(self):
        """Test that queue values are resolved"""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<env_workflow>
  <group id="case.build">
    <entry id="queue" value="debug">
      <type>char</type>
    </entry>
  </group>
</env_workflow>"""

        temp_file = self._create_workflow_xml(xml)
        workflow = EnvWorkflow(infile=temp_file)

        queue = workflow.get_queue("case.build")
        self.assertEqual(queue, "debug")


if __name__ == "__main__":
    unittest.main()
