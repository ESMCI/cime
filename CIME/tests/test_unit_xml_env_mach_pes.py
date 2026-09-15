#!/usr/bin/env python3

import pytest

from CIME.XML.env_mach_pes import EnvMachPes

XML_MACH_PES = """<?xml version="1.0"?>
<file id="env_mach_pes.xml" version="2.0">
  <header>test env_mach_pes.xml</header>
  <group id="mach_pes">
    <entry id="ESMF_AWARE_THREADING" value="{esmf_aware_threading}">
      <type>logical</type>
      <desc>TRUE indicates that the ESMF Aware threading method is used</desc>
    </entry>
  </group>
</file>
"""


@pytest.mark.parametrize(
    "comp_interface, esmf_aware_threading, expected",
    [
        # ESMF provides the threads, the batch system must see one core per task
        ("nuopc", "TRUE", 1),
        # without ESMF-aware threading the batch system requests the threads
        ("nuopc", "FALSE", 4),
        # the flag only has meaning with the nuopc interface
        ("mct", "TRUE", 4),
    ],
)
def test_get_batch_thread_count(
    tmp_path, comp_interface, esmf_aware_threading, expected
):
    infile = tmp_path / "env_mach_pes.xml"
    infile.write_text(XML_MACH_PES.format(esmf_aware_threading=esmf_aware_threading))
    env_mach_pes = EnvMachPes(
        infile=str(infile), read_only=True, comp_interface=comp_interface
    )

    assert env_mach_pes.get_batch_thread_count(4) == expected
