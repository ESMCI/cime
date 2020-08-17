"""
Interface to the streams.xml style files.  This class inherits from GenericXML.py

stream files predate cime and so do not conform to entry id format
"""
import datetime
import re
import hashlib

from CIME.XML.standard_module_setup import *
from CIME.XML.generic_xml import GenericXML
from CIME.XML.files import Files
from CIME.utils import expect

logger = logging.getLogger(__name__)

_var_ref_re = re.compile(r"\$(\{)?(?P<name>\w+)(?(1)\})")

_ymd_re = re.compile(r"%(?P<digits>[1-9][0-9]*)?y(?P<month>m(?P<day>d)?)?")

_stream_nuopc_file_template = """
  <stream_info name="{streamname}">
   <taxmode>{stream_taxmode}</taxmode>
   <tInterpAlgo>{stream_tintalgo}</tInterpAlgo>
   <readMode>{stream_readmode}</readMode>
   <mapalgo>{stream_mapalgo}</mapalgo>
   <dtlimit>{stream_dtlimit}</dtlimit>
   <yearFirst>{stream_year_first}</yearFirst>
   <yearLast>{stream_year_last}</yearLast>
   <yearAlign>{stream_year_align}</yearAlign>
   <stream_vectors>{stream_vectors}</stream_vectors>
   <stream_mesh_file>{stream_meshfile}</stream_mesh_file>
   <stream_lev_dimname>{stream_lev_dimname}</stream_lev_dimname>
   <stream_data_files>
      {stream_datafiles}
   </stream_data_files>
   <stream_data_variables>
      {stream_datavars}
   </stream_data_variables>
   <stream_offset>{stream_offset}</stream_offset>
 </stream_info>

"""
        
class StreamCDEPS(GenericXML):

    def __init__(self, infile):
        """
        Initialize a CDEPS stream object
        """
        schema = os.path.join(get_cime_root(), "config", "xml_schemas", "stream_cdeps_v2.0.xsd")
        logger.debug("Verifying using schema {}".format(schema))
        GenericXML.__init__(self, infile, schema)
        if os.path.exists(infile):
            GenericXML.read(self, infile, schema)

    def create_stream_xml(self, stream_names, case, streams_xml_file, data_list_file):
        """
        Create the stream xml file and append the required stream input data to the input data list file
        """
        # write header of stream file
        with open(streams_xml_file, 'w') as stream_file:
            stream_file.write('<?xml version="1.0"?>\n')
            stream_file.write('<file id="stream" version="2.0">\n')
        # write contents of stream file
        for stream_name in stream_names:
            if stream_name:
                self.stream_nodes = super(StreamCDEPS,self).get_child("stream_entry", {"name" : stream_name}, 
                                                                     err_msg="No stream_entry {} found".format(stream_name))

            # determine stream_year_first and stream_year_list
            data_year_first,data_year_last = self._get_stream_first_and_last_dates(self.stream_nodes, case)

            # now write the data model streams xml file
            stream_vars = {}
            stream_vars['streamname'] = stream_name
            attributes = {}
            for node in self.get_children(root=self.stream_nodes):
                node_name = node.xml_element.tag
                if node_name == 'stream_meshfile':
                    # Get the stream meshfile and resolve any xml variable dependencies
                    attributes['grid'] = case.get_value("GRID")
                    stream_meshfile = self._get_value_match(node, 'file', attributes=attributes)
                    stream_meshfile = self._resolve_values(case, stream_meshfile)
                    stream_meshfile = stream_meshfile.strip()
                    stream_vars[node_name] = stream_meshfile

                elif node_name == 'stream_datavars':
                    # Get the resolved stream data variables
                    stream_vars[node_name] = None
                    for child in self.get_children(root=node):
                        datavars = child.xml_element.text.strip()
                        datavars = self._resolve_values(case, datavars)
                        datavars = self._sub_glc_fields(datavars, case)
                        datavars = self._add_xml_delimiter(datavars.split("\n"), "var")
                        if stream_vars[node_name]:
                            stream_vars[node_name] = stream_vars[node_name] + "\n      " + datavars.strip()
                        else:
                            stream_vars[node_name] = datavars.strip()
                        # endif

                elif node_name == 'stream_datafiles':
                    # Get the resolved stream data files
                    stream_vars[node_name] = ""
                    for child in self.get_children(root=node):
                        stream_datafiles = child.xml_element.text
                        stream_datafiles = self._resolve_values(case, stream_datafiles)
                        if 'first_year' in child.xml_element.attrib and 'last_year' in child.xml_element.attrib:
                            stream_year_first= int(child.xml_element.get('first_year'))
                            stream_year_last = int(child.xml_element.get('last_year'))
                            year_first = max(stream_year_first, data_year_first)
                            year_last = min(stream_year_last, data_year_last)
                            stream_datafiles = self._sub_paths(stream_datafiles, year_first, year_last)
                        # endif
                        stream_datafiles = stream_datafiles.strip()
                        stream_vars[node_name] = self._add_xml_delimiter(stream_datafiles.split("\n"), "file")
                elif node_name.strip():
                    # Get the other dependencies
                    stream_dict = self._add_value_to_dict(stream_vars, case, node)
                        
            # append to stream xml file
            stream_file_text = _stream_nuopc_file_template.format(**stream_vars)
            with open(streams_xml_file, 'a') as stream_file:
                stream_file.write(stream_file_text)

            # append to input_data_list
            self._add_entries_to_inputdata_list(stream_meshfile, stream_datafiles, data_list_file)

        # write close of stream xml file
        with open(streams_xml_file, 'a') as stream_file:
            stream_file.write("</file>\n")

    def _get_stream_first_and_last_dates(self, stream, case):
        """
        Get first and last dates for data for the stream file
        """
        for node in self.get_children(root=stream):
            if node.xml_element.tag == 'stream_year_first':
                data_year_first = node.xml_element.text.strip()
                data_year_first = int(self._resolve_values(case, data_year_first))
            if node.xml_element.tag == 'stream_year_last':
                data_year_last = node.xml_element.text.strip()
                data_year_last = int(self._resolve_values(case, data_year_last))
        return data_year_first, data_year_last

    def _add_entries_to_inputdata_list(self, stream_meshfile, stream_datafiles, data_list_file):
        """
        Appends input data information entries to input data list file
        and writes out the new file
        """
        lines_hash = self._get_input_file_hash(data_list_file)
        with open(data_list_file, 'a') as input_data_list:
            # write out the mesh file separately
            string = "mesh = {}\n".format(stream_meshfile)
            hashValue = hashlib.md5(string.rstrip().encode('utf-8')).hexdigest()
            if hashValue not in lines_hash:
                input_data_list.write(string)
            # now append the stream_datafile entries
            for i, filename in enumerate(stream_datafiles.split("\n")):
                if filename.strip() == '':
                    continue
                string = "file{:d} = {}\n".format(i+1, filename)
                hashValue = hashlib.md5(string.rstrip().encode('utf-8')).hexdigest()
                if hashValue not in lines_hash:
                    input_data_list.write(string)

    def _get_input_file_hash(self, data_list_file):
        """
        Determine a hash for the input data file
        """
        lines_hash = set()
        if os.path.isfile(data_list_file):
            with open(data_list_file, "r") as input_data_list:
                for line in input_data_list:
                    hashValue = hashlib.md5(line.rstrip().encode('utf-8')).hexdigest()
                    logger.debug( "Found line {} with hash {}".format(line,hashValue))
                    lines_hash.add(hashValue)
        return lines_hash

    def _get_value_match(self, node, child_name, attributes=None, exact_match=False):
        '''
        Get the first best match for multiple tags in child_name based on the 
        attributes input

        <values...>
          <value A="a1">X</value>
          <value A="a2">Y</value>
          <value A="a3" B="b1">Z</value>
         </values>
        </values>
        '''
        # Store nodes that match the attributes and their scores.
        matches = []
        nodes = self.get_children(child_name, root=node)
        for vnode in nodes:
            # For each node in the list start a score.
            score = 0
            if attributes:
                for attribute in self.attrib(vnode).keys():
                    # For each attribute, add to the score.
                    score += 1
                    # If some attribute is specified that we don't know about,
                    # or the values don't match, it's not a match we want.
                    if exact_match:
                        if attribute not in attributes or \
                                attributes[attribute] != self.get(vnode, attribute):
                            score = -1
                            break
                    else:
                        if attribute not in attributes or not \
                                re.search(self.get(vnode, attribute),attributes[attribute]):
                            score = -1
                            break

            # Add valid matches to the list.
            if score >= 0:
                matches.append((score, vnode))

        if not matches:
            return None

        # Get maximum score using either a "last" or "first" match in case of a tie
        max_score = -1
        mnode = None
        for score,node in matches:
            # take the *first* best match
            if score > max_score:
                max_score = score
                mnode = node

        return self.text(mnode)

    def _add_value_to_dict(self, stream_dict, case, node):
        """
        Adds a value to the input stream dictionary needed for the
        stream file output Returns the uppdated stream_dict
        """
        name = node.xml_element.tag
        value = node.xml_element.text
        value = self._resolve_values(case, value)
        stream_dict[name] = value
        return stream_dict

    def _resolve_values(self, case, value):
        """
        Substitues $CASEROOT env_xxx.xml variables if they appear in "value"
        Returns a string
        """
        match = _var_ref_re.search(value)
        while match:
            env_val = case.get_value(match.group('name'))
            expect(env_val is not None,
                   "Namelist default for variable {} refers to unknown XML variable {}.".
                   format(value, match.group('name')))
            value = value.replace(match.group(0), str(env_val), 1)
            match = _var_ref_re.search(value)
        return value

    def _sub_glc_fields(self, datavars, case):
        """Substitute indicators with given values in a list of fields.

        Replace any instance of the following substring indicators with the
        appropriate values:
            %glc = two-digit GLC elevation class from 00 through glc_nec

        The difference between this function and `_sub_paths` is that this
        function is intended to be used for variable names (especially from the
        `strm_datvar` defaults), whereas `_sub_paths` is intended for use on
        input data file paths.

        Returns a string.

        Example: If `_sub_fields` is called with an array containing two
        elements, each of which contains two strings, and glc_nec=3:
             foo               bar
             s2x_Ss_tsrf%glc   tsrf%glc
         then the returned array will be:
             foo               bar
             s2x_Ss_tsrf00     tsrf00
             s2x_Ss_tsrf01     tsrf01
             s2x_Ss_tsrf02     tsrf02
             s2x_Ss_tsrf03     tsrf03
        """
        lines = datavars.split("\n")
        new_lines = []
        for line in lines:
            if not line:
                continue
            if "%glc" in line:
                if case.get_value('GLC_NEC') == 0:
                    glc_nec_indices = []
                else:
                    glc_nec_indices = range(case.get_value('GLC_NEC')+1)
                for i in glc_nec_indices:
                    new_lines.append(line.replace("%glc", "{:02d}".format(i)))
            else:
                new_lines.append(line)
        return "\n".join(new_lines)

    @staticmethod
    def _days_in_month(month, year=1):
        """Number of days in the given month (specified as an int, 1-12).

        The `year` argument gives the year for which to request the number of
        days, in a Gregorian calendar. Defaults to `1` (not a leap year).
        """
        month_start = datetime.date(year, month, 1)
        if month == 12:
            next_year = year+1
            next_month = 1
        else:
            next_year = year
            next_month = month + 1
        next_month_start = datetime.date(next_year, next_month, 1)
        return (next_month_start - month_start).days

    def _sub_paths(self, filenames, year_start, year_end):
        """Substitute indicators with given values in a list of filenames.

        Replace any instance of the following substring indicators with the
        appropriate values:
            %y    = year from the range year_start to year_end
            %ym   = year-month from the range year_start to year_end with all 12
                    months
            %ymd  = year-month-day from the range year_start to year_end with
                    all 12 months

        For the date indicators, the year may be prefixed with a number of
        digits to use (the default is 4). E.g. `%2ymd` can be used to change the
        number of year digits from 4 to 2.

        Note that we assume that there is no mixing and matching of date
        indicators, i.e. you cannot use `%4ymd` and `%2y` in the same line. Note
        also that we use a no-leap calendar, i.e. every month has the same
        number of days every year.

        The difference between this function and `_sub_fields` is that this
        function is intended to be used for file names (especially from the
        `strm_datfil` defaults), whereas `_sub_fields` is intended for use on
        variable names.

        Returns a string (filenames separated by newlines).
        """
        lines = [line for line in filenames.split("\n") if line]
        new_lines = []
        for line in lines:
            match = _ymd_re.search(filenames)
            if match is None:
                new_lines.append(line)
                continue
            if match.group('digits'):
                year_format = "{:0"+match.group('digits')+"d}"
            else:
                year_format = "{:04d}"
            for year in range(year_start, year_end+1):
                if match.group('day'):
                    for month in range(1, 13):
                        days = self._days_in_month(month)
                        for day in range(1, days+1):
                            date_string = (year_format + "-{:02d}-{:02d}").format(year, month, day)
                            new_line = line.replace(match.group(0), date_string)
                            new_lines.append(new_line)
                elif match.group('month'):
                    for month in range(1, 13):
                        date_string = (year_format + "-{:02d}").format(year, month)
                        new_line = line.replace(match.group(0), date_string)
                        new_lines.append(new_line)
                else:
                    date_string = year_format.format(year)
                    new_line = line.replace(match.group(0), date_string)
                    new_lines.append(new_line)
        return "\n".join(new_lines)

    @staticmethod
    def _add_xml_delimiter(list_to_deliminate, delimiter):
        expect(delimiter and not " " in delimiter, "Missing or badly formed delimiter")
        pred = "<{}>".format(delimiter)
        postd = "</{}>".format(delimiter)
        for n,item in enumerate(list_to_deliminate):
            if item.strip():
                list_to_deliminate[n] = pred + item.strip() + postd
        return "\n      ".join(list_to_deliminate)


