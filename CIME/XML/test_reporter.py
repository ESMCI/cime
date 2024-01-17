"""
Interface to the testreporter xml.  This class inherits from GenericXML.py

"""
# pylint: disable=import-error
import urllib.parse
import urllib.request
from CIME.XML.standard_module_setup import *
from CIME.XML.generic_xml import GenericXML
import ssl

# pylint: disable=protected-access
ssl._create_default_https_context = ssl._create_unverified_context


class TestReporter(GenericXML):
    def __init__(self):
        """
        initialize an object
        """
        self.root = None

        GenericXML.__init__(
            self,
            root_name_override="testrecord",
            read_only=False,
            infile="TestRecord.xml",
        )

    def setup_header(
        self, tagname, machine, compiler, mpilib, testroot, testtype, baseline
    ):
        #
        # Create the XML header that the testdb is expecting to recieve
        #
        for name, text, attribs in [
            ("tag_name", tagname, None),
            ("mach", machine, None),
            ("compiler", compiler, {"version": ""}),
            ("mpilib", mpilib, {"version": ""}),
            ("testroot", testroot, None),
            ("testtype", testtype, None),
            ("baselinetag", baseline, None),
        ]:
            self.make_child(name, attributes=attribs, text=text)

    def add_result(self, test_name, test_status):
        #
        # Add a test result to the XML structure.
        #
        tlelem = self.make_child("tests", {"testname": test_name})

        for attrib_name, text in [
            ("casestatus", None),
            ("comment", test_status["COMMENT"]),
            ("compare", test_status["BASELINE"]),
            ("memcomp", test_status["MEMCOMP"]),
            ("memleak", test_status["MEMLEAK"]),
            ("nlcomp", test_status["NLCOMP"]),
            ("status", test_status["STATUS"]),
            ("tputcomp", test_status["TPUTCOMP"]),
        ]:

            self.make_child(
                "category", attributes={"name": attrib_name}, text=text, root=tlelem
            )

    def push2testdb(self):
        #
        # Post test result XML to CESM test database
        #
        xmlstr = self.get_raw_record()
        username = input("Username:")
        os.system("stty -echo")
        password = input("Password:")
        os.system("stty echo")
        print()
        params = {"username": username, "password": password, "testXML": xmlstr}
        url = "https://csegweb.cgd.ucar.edu/testdb/cgi-bin/processXMLtest.cgi"
        data = urllib.parse.urlencode(params)
        data = data.encode("ascii")
        req = urllib.request.Request(url, data)
        result = urllib.request.urlopen(req)
        print(result.read())
