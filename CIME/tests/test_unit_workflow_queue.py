#!/usr/bin/env python3

"""
Unit tests for workflow queue selection functionality
"""

import os
import tempfile
import unittest
from unittest import mock

from CIME.XML.workflow import Workflow


class TestWorkflowQueue(unittest.TestCase):
    """Test cases for workflow queue functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_files = []

    def tearDown(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def _create_workflow_xml(self, content):
        """Helper to create a temporary workflow XML file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(content)
            temp_file = f.name
        self.temp_files.append(temp_file)
        return temp_file

    def test_job_level_queue(self):
        """Test queue specified at job level"""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<config_workflow version="2.0">
  <workflow_jobs id="default">
    <job name="case.build">
      <template>dummy_template</template>
      <queue>debug</queue>
      <prereq>TRUE</prereq>
    </job>
    <job name="case.run">
      <template>dummy_template2</template>
      <prereq>TRUE</prereq>
    </job>
  </workflow_jobs>
</config_workflow>"""

        temp_file = self._create_workflow_xml(xml)
        workflow = Workflow(infile=temp_file)

        class MockCase:
            def get_value(self, var):
                if var == "MACH":
                    return "test_machine"
                return None

        case = MockCase()

        # Test job with queue specified
        queue = workflow.get_queue(case, "case.build", machine="test_machine")
        self.assertEqual(queue, "debug")

        # Test job without queue specified
        queue = workflow.get_queue(case, "case.run", machine="test_machine")
        self.assertIsNone(queue)

    def test_machine_specific_queue(self):
        """Test queue specified at runtime_parameters level for specific machine"""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<config_workflow version="2.0">
  <workflow_jobs id="default">
    <job name="case.build">
      <template>dummy_template</template>
      <prereq>TRUE</prereq>
      <runtime_parameters MACH="machine1">
        <queue>debug</queue>
      </runtime_parameters>
      <runtime_parameters MACH="machine2">
        <queue>short</queue>
      </runtime_parameters>
    </job>
  </workflow_jobs>
</config_workflow>"""

        temp_file = self._create_workflow_xml(xml)
        workflow = Workflow(infile=temp_file)

        class MockCase:
            def get_value(self, var):
                if var == "MACH":
                    return "machine1"
                return None

        case = MockCase()

        # Test machine-specific queue
        queue = workflow.get_queue(case, "case.build", machine="machine1")
        self.assertEqual(queue, "debug")

        queue = workflow.get_queue(case, "case.build", machine="machine2")
        self.assertEqual(queue, "short")

    def test_job_level_overrides_runtime_parameters(self):
        """Test that job-level queue takes precedence over runtime_parameters"""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<config_workflow version="2.0">
  <workflow_jobs id="default">
    <job name="case.build">
      <template>dummy_template</template>
      <queue>job_level</queue>
      <prereq>TRUE</prereq>
      <runtime_parameters MACH="machine1">
        <queue>runtime_level</queue>
      </runtime_parameters>
    </job>
  </workflow_jobs>
</config_workflow>"""

        temp_file = self._create_workflow_xml(xml)
        workflow = Workflow(infile=temp_file)

        class MockCase:
            def get_value(self, var):
                if var == "MACH":
                    return "machine1"
                return None

        case = MockCase()

        # Job-level queue should be found first
        queue = workflow.get_queue(case, "case.build", machine="machine1")
        self.assertEqual(queue, "job_level")

    def test_no_queue_specified(self):
        """Test behavior when no queue is specified"""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<config_workflow version="2.0">
  <workflow_jobs id="default">
    <job name="case.run">
      <template>dummy_template</template>
      <prereq>TRUE</prereq>
    </job>
  </workflow_jobs>
</config_workflow>"""

        temp_file = self._create_workflow_xml(xml)
        workflow = Workflow(infile=temp_file)

        class MockCase:
            def get_value(self, var):
                if var == "MACH":
                    return "test_machine"
                return None

        case = MockCase()

        # Should return None when no queue is specified
        queue = workflow.get_queue(case, "case.run", machine="test_machine")
        self.assertIsNone(queue)

    def test_queue_in_get_workflow_jobs(self):
        """Test that queue is included in job configuration from get_workflow_jobs"""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<config_workflow version="2.0">
  <workflow_jobs id="default">
    <job name="case.build">
      <template>dummy_template</template>
      <queue>debug</queue>
      <prereq>TRUE</prereq>
    </job>
    <job name="case.run">
      <template>dummy_template2</template>
      <prereq>TRUE</prereq>
      <runtime_parameters MACH="machine1">
        <queue>gpu</queue>
      </runtime_parameters>
    </job>
  </workflow_jobs>
</config_workflow>"""

        temp_file = self._create_workflow_xml(xml)
        workflow = Workflow(infile=temp_file)

        jobs = workflow.get_workflow_jobs("machine1")
        job_dict = {name: config for name, config in jobs}

        # Check that queue is in the job configuration
        self.assertIn("queue", job_dict["case.build"])
        self.assertEqual(job_dict["case.build"]["queue"], "debug")

        self.assertIn("queue", job_dict["case.run"])
        self.assertEqual(job_dict["case.run"]["queue"], "gpu")


if __name__ == "__main__":
    unittest.main()
