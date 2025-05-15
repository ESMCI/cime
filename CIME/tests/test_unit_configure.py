import os
import unittest
import tempfile
import shutil

from CIME.utils import expect

from CIME.BuildTools.configure import generate_env_mach_specific 
from CIME.XML.machines import Machines

class TestConfigure(unittest.TestCase):

    def setUp(self):
        self.compiler = "intel"
        self.mpilib = "mpich"
        self.debug = "FALSE"
        self.comp_interface = "nuopc"
        self.sysos = "CNL"
        mach = "derecho"

        self.mach_obj = Machines(machine=mach)

        self.tempdir = tempfile.mkdtemp()
        self.caseroot = os.path.join( self.tempdir, "newcase" )
        os.mkdir( self.caseroot )
        self.cwd = os.getcwd()
        os.chdir( self.caseroot )

    def tearDown(self):
        # Make sure we aren't in the temp directory to remove
        
        os.chdir( self.cwd )
        if os.getcwd() == self.tempdir:
            expect( False, "CWD is the tempdir to be removed" )
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_generate_env_mach_specific(self):

        generate_env_mach_specific(
              self.caseroot,
              self.mach_obj,
              self.compiler,
              self.mpilib,
              self.debug,
              self.comp_interface,
              self.sysos,
              unit_testing = False,
              threaded = False
          )

