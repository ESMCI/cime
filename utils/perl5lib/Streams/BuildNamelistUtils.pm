package BuildNamelistUtils;
my $pkg_nm = 'buildNamelistUtils';

use strict;
use English;
use Cwd qw( getcwd abs_path chdir);
use IO::File;
use Data::Dumper;
use List::Util qw ( max );
use Log::Log4perl qw(get_logger);
use Build::Config;
use Build::NamelistDefinition;
use Build::NamelistDefaults;
use Build::Namelist;
use Config::SetupTools;

my $logger;

BEGIN{
    $logger = get_logger();
}

#-----------------------------------------------------------------------------------------------
sub create_namelist_objects {

    my $comp		= shift;
    my $cimeroot	= shift;
    my $caseroot	= shift;
    my $confdir		= shift;
    my $user_xml_dir	= shift;
    my $infile		= shift;

    my $nl_definition_file = "$cimeroot/components/data_comps/${comp}/bld/namelist_files/namelist_definition_${comp}.xml";
    if (defined $user_xml_dir) {
	# user has user namelist definition files
	my $filename = $nl_definition_file;
	$filename    =~ s!(.*)/!!;
	my $newfile  = "${user_xml_dir}/$filename";
	if ( -f "$newfile" ) {
	    $nl_definition_file = $newfile;
	}
    }
    (-f "$nl_definition_file")  or  die "** Cannot find namelist definition file \"$nl_definition_file\" **";


    my @nl_defaults_files = ( "$cimeroot/components/data_comps/${comp}/bld/namelist_files/namelist_defaults_${comp}.xml");
    if (defined $user_xml_dir) {
	# user has user namelist defaults files
	my @filelist = @nl_defaults_files;
	foreach my $file  ( @filelist ) {
	    $file =~ s!(.*)/!!;
	    my $newfile = "${user_xml_dir}/$file";
	    if ( -f "$newfile" ) {
		unshift @nl_defaults_files, $newfile;
	    }
	}
    }
    foreach my $nl_defaults_file ( @nl_defaults_files ) {
	(-f "$nl_defaults_file")  or  die "** Cannot find namelist defaults file \"$nl_defaults_file\" **";
	# print "Using namelist defaults file $nl_defaults_file$eol"; }
    }

    # build empty config_cache.xml file 
    my $config_cache = "$confdir/config_cache.xml";
    my  $fh = new IO::File;
    $fh->open(">$config_cache") or die "** can't open file: $config_cache\n";
    print $fh  <<"EOF";
<?xml version="1.0"?>
<config_definition>
</config_definition>
EOF
    $fh->close;
    my $cfg        = Build::Config->new( $config_cache );
    my $definition = Build::NamelistDefinition->new( $nl_definition_file );
    my $defaults   = Build::NamelistDefaults->new( shift( @nl_defaults_files ), $cfg);
    foreach my $nl_defaults_file ( @nl_defaults_files ) {
	$defaults->add( "$nl_defaults_file" );
    }
    my $nl = Build::Namelist->new();

    # Process $infile
    if (defined $infile) {
	foreach my $file ( split( /,/, $infile ) ) {
	    # Parse namelist input from a file
	    my $nl_infile = Build::Namelist->new($file);

	    # Validate input namelist -- trap exceptions
	    my $nl_infile_valid;
	    eval { $nl_infile_valid = $definition->validate($nl_infile); };
	    if ($@) {
		die "ERROR: Invalid namelist variable in '-infile' $infile.\n $@";
	    }

	    # Merge input values into namelist.  Previously specified values have higher precedence
	    # and are not overwritten.
	    $nl->merge_nl($nl_infile_valid);
	}
    }

    return $definition, $defaults, $nl;
}

#-----------------------------------------------------------------------------------------------
sub create_stream_file{

    my ($caseroot, $confdir, $xmlvars, $defaults, 
	$namelist_opts, $stream_template_opts, $streams_namelists, 
	$stream, $streamfile, $fh_out) = @_;

    if (-e "$caseroot/user_$streamfile") {
        if ( ! -w "$caseroot/user_$streamfile" ) {
           print "Your user streams file is read-only: $caseroot/user_$streamfile\n";
           die "Make it writable to continue\n";
        }
	my $command = "cp -p $caseroot/user_$streamfile $confdir/$streamfile";
	system($command) == 0  or die "system $command failed: $? \n";
	return
    }


    my %template;
    $template{'offset'}           = $defaults->get_value( "strm_offset"    , $namelist_opts);
    $template{'data_filepath'}    = $defaults->get_value( "strm_datdir"    , $namelist_opts);
    $template{'data_filenames'}   = $defaults->get_value( "strm_datfil"    , $namelist_opts);
    $template{'data_varnames'}    = $defaults->get_value( "strm_datvar"    , $namelist_opts);
    $template{'domain_filepath'}  = $defaults->get_value( "strm_domdir"    , $namelist_opts);
    $template{'domain_filenames'} = $defaults->get_value( "strm_domfil"    , $namelist_opts);
    $template{'domain_varnames'}  = $defaults->get_value( "strm_domvar"    , $namelist_opts);
    $template{'yearfirst'}        = $defaults->get_value( "strm_year_start", $namelist_opts);
    $template{'yearlast'}         = $defaults->get_value( "strm_year_end"  , $namelist_opts);

    $template{'data_filepath'}    = SetupTools::expand_xml_var( $template{'data_filepath'}   , $xmlvars );
    $template{'data_filenames'}   = SetupTools::expand_xml_var( $template{'data_filenames'}  , $xmlvars );
    $template{'domain_filepath'}  = SetupTools::expand_xml_var( $template{'domain_filepath'} , $xmlvars );
    $template{'domain_filenames'} = SetupTools::expand_xml_var( $template{'domain_filenames'}, $xmlvars );
    $template{'yearfirst'}        = SetupTools::expand_xml_var( $template{'yearfirst'}       , $xmlvars );
    $template{'yearlast'}         = SetupTools::expand_xml_var( $template{'yearlast'}        , $xmlvars );

    # Overwrite %template with values from %stream_template_opts passed in 
    foreach my $key (keys %$stream_template_opts) {
	$template{$key} = $$stream_template_opts{$key};
    }

    # Consistency check
    foreach my $item ( "yearfirst", "yearlast", "offset", 
		       "data_filepath", "data_filenames", "data_varnames",
		       "domain_filepath", "domain_filenames", "domain_varnames") {
	if ( $template{$item} =~ /^[ ]*$/ ) {
	    die "ERROR:: bad $item for stream:  $stream\n";
	}
    }

    # Write stream file
    my $fh = new IO::File;
    if ( $streamfile ne "" ) {
	$fh->open(">$streamfile") or die "** can't open output stream file: $streamfile, $!\n";
	print "Opening output stream file: $streamfile\n" ;

	print $fh "<dataSource> \n";
	print $fh "   GENERIC \n";
	print $fh "</dataSource> \n";
	print $fh "<domainInfo> \n";
	print $fh "  <variableNames>";
	print $fh "     $template{'domain_varnames'}";
	print $fh "  </variableNames> \n";
	print $fh "  <filePath> \n";
	print $fh "     $template{'domain_filepath'} \n";
	print $fh "  </filePath> \n";
	print $fh "  <fileNames> \n";
	print $fh "     $template{'domain_filenames'}\n";  
	print $fh "  </fileNames> \n";    
	print $fh "</domainInfo> \n";

	print $fh "<fieldInfo> \n";
	print $fh "   <variableNames>";
	print $fh "      $template{'data_varnames'}"; 
	print $fh "   </variableNames> \n";
	print $fh "   <filePath> \n";
	print $fh "      $template{'filepath'} \n";
	print $fh "   </filePath> \n";
	print $fh "   <fileNames> \n";
	print $fh "      $template{'filenames'} \n";
	print $fh "   </fileNames> \n";
	print $fh "   <offset> \n";
	print $fh "      $template{'offset'} \n";
	print $fh "   </offset> \n";
	print $fh "</fieldInfo> \n";

	$fh->close();
    }
    
    # Update the component input_data_list in Buildconf/
    my $i = 0;
    my @filenames = $template{'domain_filenames'};
    my $filepath = $template{'domain_filepath'};
    foreach my $file ( @filenames) {
     	$i++;
	my $subfile = Sub($file);
     	print $fh_out "domain${i} = ${filepath}/${file}\n";
     }
    my $i = 0;
    my @filenames = $template{'data_filenames'};
    my $filepath = $template{'data_filepath'};
    foreach my $file ( @filenames) {
     	$i++;
     	print $fh_out "file${i} = ${filepath}/${file}\n";
     }

    # Update the streams_namelists hash for the new stream
    update_streams_namelists($defaults, $namelist_opts, 
			     $xmlvars, $stream, $streamfile, $streams_namelists);

}


#-----------------------------------------------------------------------------------------------
sub update_streams_namelists {

    my $defaults	  = shift;
    my $namelist_opts	  = shift;
    my $xmlvars		  = shift;
    my $stream		  = shift; 
    my $streamfile	  = shift;
    my $streams_namelists = shift;

    # Stream specific namelist variables used below for $nl
    my $tintalgo   = $defaults->get_value( "strm_tintalgo"  , $namelist_opts);
    my $mapalgo    = $defaults->get_value( 'strm_mapalgo'   , $namelist_opts);
    my $mapmask    = $defaults->get_value( 'strm_mapmask'   , $namelist_opts);
    my $taxmode    = $defaults->get_value( "strm_taxmode"   , $namelist_opts);
    my $fillalgo   = $defaults->get_value( 'strm_fillalgo'  , $namelist_opts);
    my $fillmask   = $defaults->get_value( 'strm_fillmask'  , $namelist_opts);
    my $dtlimit    = $defaults->get_value( 'strm_dtlimit'   , $namelist_opts);
    my $beg_year   = $defaults->get_value( 'strm_year_start', $namelist_opts);
    my $end_year   = $defaults->get_value( 'strm_year_end'  , $namelist_opts);
    my $align_year = $defaults->get_value( 'strm_year_align', $namelist_opts);

    $beg_year      = SetupTools::expand_xml_var($beg_year,   $xmlvars );
    $end_year      = SetupTools::expand_xml_var($end_year,   $xmlvars );
    $align_year    = SetupTools::expand_xml_var($align_year, $xmlvars );

    foreach my $year ( $beg_year, $end_year, $align_year ) {
       if ( $year eq "" || $year !~ /[0-9]+/ ) {
	   print "\n\nyear=$year is NOT set or NOT an integer\n";
	   die "ERROR:: bad year to run stream over: $stream\n";
       }
    }
    if ( $beg_year > $end_year ) {
	print "\n\nbeg_year=$beg_year end_year=$end_year\n";
	die "ERROR:: beg_year greater than end_year\n";
    }

    if ( ! defined($$streams_namelists{"ostreams"}))  {
	$$streams_namelists{"ostreams"}	 = "\"$streamfile $align_year $beg_year $end_year\"";
	$$streams_namelists{"omapalgo"}	 = "\'$mapalgo\'";
	$$streams_namelists{"omapmask"}	 = "\'$mapmask\'";
	$$streams_namelists{"otintalgo"} = "\'$tintalgo\'";
	$$streams_namelists{"otaxmode"}	 = "\'$taxmode\'";
	$$streams_namelists{"ofillalgo"} = "\'$fillalgo\'";
	$$streams_namelists{"ofillmask"} = "\'$fillmask\'";
	$$streams_namelists{"odtlimit"}	 = "$dtlimit";
    } else {
	my $ostreams =  $$streams_namelists{"ostreams"} ;
	$$streams_namelists{"ostreams"}   = "$ostreams,\"$streamfile $align_year $beg_year $end_year\"";
	$$streams_namelists{"omapalgo"}  .= ",\'$mapalgo\'";
	$$streams_namelists{"omapmask"}  .= ",\'$mapmask\'";
	$$streams_namelists{"otintalgo"} .= ",\'$tintalgo\'";
	$$streams_namelists{"otaxmode"}  .= ",\'$taxmode\'";
	$$streams_namelists{"ofillalgo"} .= ",\'$fillalgo\'";
	$$streams_namelists{"ofillmask"} .= ",\'$fillmask\'";
	$$streams_namelists{"odtlimit"}  .= ",$dtlimit";
    }
}


#-----------------------------------------------------------------------------------------------
sub add_default {

    # Add a value for the specified variable to the specified namelist object.  The variables
    # already in the object have the higher precedence, so if the specified variable is already
    # defined in the object then don't overwrite it, just return.
    #
    # This method checks the definition file and adds the variable to the correct
    # namelist group.
    #
    # The value can be provided by using the optional argument key 'val' in the
    # calling list.  Otherwise a default value is obtained from the namelist
    # defaults object.  If no default value is found this method throws an exception.
    #
    # Example 1: Specify the default value $val for the namelist variable $var in namelist
    #            object $nl:
    #
    #  add_default($definition, $defaults, $din_loc_root, $nl, $var, $value)

    my $definition	= shift;
    my $defaults	= shift;
    my $din_loc_root	= shift;
    my $nl		= shift;	# namelist object
    my $var		= shift;	# name of namelist variable
    my $value		= shift;	# value

    # If variable has quotes around it
    if ( $var =~ /'(.+)'/ ) {
       $var = $1;
    }
    # Query the definition to find which group the variable belongs to.  Exit if not found.
    my $group = $definition->get_group_name($var);
    unless ($group) {
	my $fname = $definition->get_file_name();
	die "ERROR: variable \"$var\" not found in namelist definition file $fname.\n";
    }

    # Check whether the variable has a value in the namelist object -- if so then skip to end
    my $val = $nl->get_variable_value($group, $var);
    if (! defined $val) {

       # Look for a specified value in the options hash
       if (defined $value) {
	   $val = $value;
       } else {
	   # Get a value from namelist defaults object.
	   # If the 'val' key isn't in the hash, then just pass anything else
	   # in %opts to the get_value method to be used as attributes that are matched
	   # when looking for default values.
	   my %opts; 
	   $val = $defaults->get_value($var, \%opts);
       }

       unless ( defined($val) ) {
	   die "No default value found for $var.\n" 
       }

       # query the definition to find out if the variable is an input pathname
       # If the namelist variable is defined to be an absolute pathname, then prepend
       # the inputdata root directory.
       my $is_input_pathname = $definition->is_input_pathname($var);
       if ($is_input_pathname eq 'abs') {
	   $val = set_abs_filepath($val, $din_loc_root);
	   if ( ($val !~ /null/) and (! -f "$val") ) {
	       die "File not found: $var = $val\n";
	   }
       }

       # query the definition to find out if the variable takes a string value.
       # The returned string length will be >0 if $var is a string, and 0 if not.
       # If the variable is a string, then add quotes if they're missing
       my $str_len = $definition->get_str_len($var);
       if ($str_len > 0) {
	   $val = quote_string($val);
       }

       # set the value in the namelist
       $nl->set_variable_value($group, $var, $val);
    }

}

#-----------------------------------------------------------------------------------------------
sub check_input_files {

    # For each variable in the namelist which is an input dataset, check to see if it
    # exists locally.

    my $definition		= shift;
    my $nl			= shift;    # namelist object
    my $inputdata_rootdir	= shift;    # if false prints test, else creates inputdata file
    my $outfile			= shift;

    open(OUTFILE, ">>$outfile") if defined $inputdata_rootdir;

    # Look through all namelist groups
    my @groups = $nl->get_group_names();
    foreach my $group (@groups) {

	# Look through all variables in each group
	my @vars = $nl->get_variable_names($group);
	foreach my $var (@vars) {

	    # Is the variable an input dataset?
	    my $input_pathname_type = $definition->is_input_pathname($var);

	    # If it is, check whether it exists locally and print status
	    if ($input_pathname_type) {

		# Get pathname of input dataset
		my $pathname = $nl->get_variable_value($group, $var);
		# Need to strip the quotes
		$pathname =~ s/[\'\"]//g;

		if ($input_pathname_type eq 'abs') {
                    if ($inputdata_rootdir) {
                        print OUTFILE "$var = $pathname\n";
                    }
                    else {
		        if (-e $pathname) {  # use -e rather than -f since the absolute pathname
			                     # might be a directory
			    print "OK -- found $var = $pathname\n";
		        }
		        else {
			    print "NOT FOUND:  $var = $pathname\n";
		        }
                    }
		}
		elsif ($input_pathname_type =~ m/rel:(.+)/o) {
		    # The match provides the namelist variable that contains the
		    # root directory for a relative filename
		    my $rootdir_var = $1;
		    my $rootdir = $nl->get_variable_value($group, $rootdir_var);
		    $rootdir =~ s/[\'\"]//g;
                    if ($inputdata_rootdir) {
                        $pathname = "$rootdir/$pathname";
                        print OUTFILE "$var = $pathname\n";
                    }
                    else {
		        if (-f "$rootdir/$pathname") {
			    print "OK -- found $var = $rootdir/$pathname\n";
		        }
		        else {
			    print "NOT FOUND:  $var = $rootdir/$pathname\n";
		        }
                    }
		}
	    }
	}
    }
    close OUTFILE if defined $inputdata_rootdir;
    return 0 if defined $inputdata_rootdir;
}

#-----------------------------------------------------------------------------------------------
sub create_shr_strdata_nml {

    my $comp			= shift;
    my $nl			= shift;
    my $defaults		= shift;
    my $definition              = shift;
    my $namelist_opts		= shift;
    my $streams_namelists	= shift;
    my $din_loc_root		= shift;
    my $domain_filename         = shift;

    my $datamode   = $defaults->get_value( "datamode", $namelist_opts );
    add_default($definition, $defaults, $din_loc_root, 
		$nl, 'datamode', "$datamode");  

    if ($comp eq 'datm') {
	my $vectors    = $defaults->get_value( "vectors",  $namelist_opts );
	add_default($definition, $defaults, $din_loc_root, 
		    $nl, 'vectors', "$vectors");
    }

    if (defined $domain_filename) {
	add_default($definition, $defaults, $din_loc_root, 
		    $nl, 'domainfile', "$domain_filename");
    }
    if ($datamode ne 'NULL') {

	add_default($definition, $defaults, $din_loc_root, 
		    $nl, 'streams', $$streams_namelists{"ostreams"});

	add_default($definition, $defaults, $din_loc_root, 
		    $nl, 'mapalgo', $$streams_namelists{"omapalgo"});

	add_default($definition, $defaults, $din_loc_root, 
		    $nl, 'mapmask', $$streams_namelists{"omapmask"});

	add_default($definition, $defaults, $din_loc_root, 
		    $nl, 'tintalgo', $$streams_namelists{"otintalgo"});

	add_default($definition, $defaults, $din_loc_root, 
		    $nl, 'taxmode', $$streams_namelists{"otaxmode"});

	add_default($definition, $defaults, $din_loc_root, 
		    $nl, 'fillalgo', $$streams_namelists{"ofillalgo"});

	add_default($definition, $defaults, $din_loc_root, 
		    $nl, 'fillmask', $$streams_namelists{"ofillmask"});

	if ($$streams_namelists{"odtlimit"} ne "") { 
	    add_default($definition, $defaults, $din_loc_root, 
			$nl, 'dtlimit', $$streams_namelists{"odtlimit"});
	}
    }
}

#-----------------------------------------------------------------------------------------------
sub write_output_files {

    my $comp		= shift;
    my $nl		= shift;
    my $definition	= shift;
    my $din_loc_root	= shift;
    my $caseroot	= shift;

    # Validate that the entire resultant namelist is valid
    $definition->validate($nl);

    # dcomp_comp_in file
    my @groups = qw(shr_strdata_nml);
    my $outfile = "./d${comp}_${comp}_in";
    $nl->write($outfile, 'groups'=>\@groups);
    #print "Writing d${comp}_dshr namelist \n"; 

    # comp_in
    @groups = ("d${comp}_nml");
    $outfile = "./d${comp}_in";
    $nl->write($outfile, 'groups'=>\@groups);
    #print "Writing d${comp}_in namelist \n";

    # comp_modelio
    @groups = qw(modelio);
    $outfile = "./${comp}_modelio.nml";
    $nl->set_variable_value( "modelio", "logfile", "'atm.log'" );
    $nl->write($outfile, 'groups'=>\@groups);
    #print "Writing ${comp}_modelio.nml namelist \n"; 

    # Test that input files exist locally.
    check_input_files($definition, $nl, $din_loc_root, 
		      "$caseroot/Buildconf/d${comp}.input_data_list");

}

#-----------------------------------------------------------------------------------------------
sub set_abs_filepath {

# check whether the input filepath is an absolute path, and if it isn't then
# prepend a root directory

    my ($filepath, $rootdir) = @_;

    # strip any leading/trailing whitespace
    $filepath =~ s/^\s+//;
    $filepath =~ s/\s+$//;
    $rootdir  =~ s/^\s+//;
    $rootdir  =~ s/\s+$//;

    # strip any leading/trailing quotes
    $filepath =~ s/^['"]+//;
    $filepath =~ s/["']+$//;
    $rootdir =~ s/^['"]+//;
    $rootdir =~ s/["']+$//;

    my $out = $filepath;
    unless ( $filepath =~ /^\// ) {  # unless $filepath starts with a /
	$out = "$rootdir/$filepath"; # prepend the root directory
    }
    return $out;
}

#-----------------------------------------------------------------------------------------------
sub valid_option {

    my ($val, @expect) = @_;
    my ($expect);

    $val =~ s/^\s+//;
    $val =~ s/\s+$//;
    foreach $expect (@expect) {
	if ($val =~ /^$expect$/i) { return $expect; }
    }
    return undef;
}

#-----------------------------------------------------------------------------------------------

sub quote_string {
    my $str = shift;
    $str =~ s/^\s+//;
    $str =~ s/\s+$//;
    unless ($str =~ /^['"]/) {        #"'
        $str = "\'$str\'";
    }
    return $str;
}

#-----------------------------------------------------------------------------------------------
sub Sub {

    # Substitute indicators with given values
    #
    # Replace any instance of the following substring indicators with the appropriate values:#
    #
    #     %y    = year from the range yearfirst to yearlast
    #     %ym   = year-month from the range yearfirst to yearlast with all 12 months
    #     %ymd  = year-month-day from the range yearfirst to yearlast with all 12 months
    #
    # fileNames or anything with %y, %ym or %ymd will be returned as a reference to an array.
    # Everything else is returned as a scalar.
    #
    # Difference between Sub and SubFields: Sub is called for anything
    # that might be filenames, and does replacements that may be
    # needed for filenames 
    # SubFields is called for the field list in datvarnames, and does
    # replacements that might be needed for this field list.
    #
    my $value     = shift;
    my $yearfirst = shift;
    my $yearlast  = shift;

    $value =~  s/^[ \n]+//;          # remove leading spaces
    $value =~  s/[ \n]+$//;          # remove ending spaces

    # Replace % indicators appropriately
    #
    # If year or year/month indicators exist
    if ( $value =~ /%([1-9]*)y([m]?)([d]?)/ ) {

	my $digits = 4;
	if ( $1 ne "" ) { $digits = $2; }
	my $months = 1;
	if ( $2 eq "" ) { $months = 0; }
	my $days   = 0;
	if ( $3 ne "" ) {
	    if ( ! $months ) {
		die "Months NOT defined but days are? (\%yd is NOT valid indicator)\n";
	    }
	    $months = 0;
	    $days   = 1;
	}
	if ( ($yearfirst < 0)  || ($yearlast < 0) ) {
	    die "yearfirst and yearlast  was NOT defined on command line and needs to be set\n";
	}
	#
	# Loop over year range
	#
	my @filenames;
	my $startfilename;
	my $endfilename;
	#
	# FIXME - this no longer seems to be used
	# Include previous December if %ym form and lastmonth is true
	#
	# if ( $lastmonth && $months ) {
	#     my $year = $yearfirst-1;
	#     my $filename = $value;
	#     my $month = 12;
	#     if ( $filename =~ /^([^%]*)%[1-9]?ym([^ ]*)$/ ) {
	# 	$startfilename = $1;
	# 	$endfilename   = $2;
	# 	$filename = sprintf "%s%${digits}.${digits}d-%2.2d%s", $startfilename,
	# 	$year, $month, $endfilename;
	# 	push @filenames, $filename;
	#     }
	# }
	# #
	# # Include previous December/31 if %ymd form and lastmonth is true
	# #
	# if ( $lastmonth && $months ) {
	#     my $year = $yearfirst-1;
	#     my $filename = $value;
	#     my $month = 12;
	#     my $day   = 31;
	#     if ( $filename =~ /^([^%]*)%[1-9]?ymd([^ ]*)$/ ) {
	# 	$startfilename = $1;
	# 	$endfilename   = $2;
	# 	$filename = sprintf "%s%${digits}.${digits}d-%2.2d-%2.2d%s", $startfilename,
	# 	$year, $month, $day, $endfilename;
	# 	push @filenames, $filename;
	#     }
	# }
	for ( my $year = $yearfirst; $year <= $yearlast; $year++ ) {
	    #
	    # If include year and months AND days
	    #
	    if ( $days ) {
		for ( my $month = 1; $month <= 12; $month++ ) {
		    my $dpm = DaysPerMonth( $month, $year );
		    for ( my $day = 1; $day <= $dpm; $day++ ) {
			my $filename = $value;
			if ( $filename =~ /^([^%]*)%[1-9]?ymd([^ ]*)$/ ) {
			    $startfilename = $1;
			    $endfilename   = $2;
			    $filename = sprintf "%s%${digits}.${digits}d-%2.2d-%2.2d%s",
			    $startfilename, $year, $month, $day, $endfilename;
			    push @filenames, $filename;
			}
		    }
		}
		#
		# If include year and months
		#
	    } elsif ( $months ) {
		for ( my $month = 1; $month <= 12; $month++ ) {
		    my $filename = $value;
		    if ( $filename =~ /^([^%]*)%[1-9]?ym([^ ]*)$/ ) {
			$startfilename = $1;
			$endfilename   = $2;
			$filename = sprintf "%s%${digits}.${digits}d-%2.2d%s", $startfilename,
			$year, $month, $endfilename;
			push @filenames, $filename;
		    }
		}
		#
		# If just years
		#
	    } else {
		my $filename = $value;
		if ( $filename =~ /^([^%]*)%[1-9]?y([^ ]*)$/ ) {
		    $startfilename = $1;
		    $endfilename   = $2;
		    $filename = sprintf "%s%${digits}.${digits}d%s", $startfilename, $year,
		    $endfilename;
		    push @filenames, $filename;
		}
	    }
	}
	if ( $#filenames < 0 ) {
	    die "No output filenames -- must be something wrong in template or input filename indicator\n";
	}
	return( \@filenames );

    } else {

	# Otherwise return a scalar value
	return( "$value" );
    }
}

#-------------------------------------------------------------------------------

sub DaysPerMonth {

    # Return the number of days per month for a given month
    # (and in general year -- but right now just do a noleap calendar of 365 days/year)

    my $month = shift;
    my $year  = shift;

    my @dpm = ( 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 );
    if ( $month < 1 || $month > 12 ) {
	die "Input month is NOT valid = $month\n";
    }
    my $days = $dpm[$month-1];
    return( $days );
}

