package ConfigCase;
my $pkg_nm = 'ConfigCase';

#-----------------------------------------------------------------------------------------------
# SYNOPSIS
# 
#   use ConfigCase;
# 
#   # create a new empty config case
#   my $cfg = ConfigCase->new("");
#
#   # set some parameters
#   $cfg->set($id, $value);
# 
#   # get some parameters
#   my $value = $cfg->get($id);
#
#   # Write an xml file out
#   $cfg->write_file("$caseroot/env_run.xml", "xml","$caseroot");
#
#   # Reset the config definition file with all of the values from the xml files
#   # in the $caseroot directory
#   $cfg->reset_setup("$caseroot/env_build.xml");
# 
# DESCRIPTION
# 
# ConfigCase objects are used to represent features of a CIME model
# configuration that must be specified when a new case is created.
#
# new() Reads xml files that contain the configuration definition and
#       default values of the configuration parameters.
#
#       The "definition.xml" file contains all the allowable
#       parameters with a description of each one.  Where appropriate a
#       list of valid values of a parameter is given.  Generic default
#       values that are useful across many model configurations are
#       provided for some parameters.
#
#       The generic default values that are provided in the definition file
#       may be overridden by values in a setup file ("config_setup.xml")
#       that is assumed to provide appropriate values for a specific model
#       configuration.  This setup file is optional.
#
# is_valid_name() 
#       Returns true if the specified parameter name is contained in
#       the configuration definition file.
#
# is_ignore_name() 
#       Returns true if the specified parameter name is a name to ignore.
#
# is_valid_value() 
#       Returns true if the specified parameter name is contained in
#       the configuration definition file, and either 1) the specified value is
#       listed as a valid_value in the definition file, or 2) the definition file
#       doesn't specify the valid values.
#
# is_char() 
#       Returns true is the specified parameter name is of character type.
#
# get() Return the value of the specified configuration parameter.  Triggers
#       an exception if the parameter name is not valid.
#       ***NOTE*** If you don't want to trap exceptions, then use the query
#                  functions before calling this routine.
#
# reset_setup() 
#       Reset with all of the values from the xml files in the $caseroot directory
# 
# set() 
#       Sets values of the configuration parameters.  It takes the
#       parameter name and its value as arguments.  An invalid parameter
#       name (i.e., a name not present in the definition file) triggers an
#       exception.  If the definition file contains valid values of a
#       parameter, then the set method checks for a valid input value.  If
#       and invalid value is found then an exception is thrown.
#       ***NOTE*** If you don't want to trap exceptions, then use the query
#                  functions before calling this routine.
#
# write_file() 
#       Write an xml file.  The first argument is the
#       filename.  The second argument, if present, is the commandline of the
#       setup command that was invoked to produce the output configuration
#       file.  It is written to the output file to help document the procedure
#       used to petsetup the executable.
#
#-----------------------------------------------------------------------------------------------

use strict;
use English;
#use warnings;
#use diagnostics;
use IO::File;
use Data::Dumper;
use XML::LibXML;
use File::Basename;

#-----------------------------------------------------------------------------------------------
# Check for the existence of XML::LibXML in whatever perl distribution happens to be in use.
# If not found, print a warning message then exit.
eval {
    require XML::LibXML;
    XML::LibXML->import();
};
if($@)
{
    my $warning = <<END;
WARNING:
  The perl module XML::LibXML is needed for XML parsing in the CIME script system.
  Please contact your local systems administrators or IT staff and have them install it for
  you, or install the module locally.  

END
    print "$warning\n";
    exit(1);
}

#-----------------------------------------------------------------------------------------------
sub new
{
    my $class = shift;
    my ($definition_file, $default_file) = @_;

    # bless the object here so the initialization has access to object methods
    my $cfg = {};
    bless( $cfg, $class );
    return $cfg;
}

#-----------------------------------------------------------------------------------------------
sub add_config_variables
{
    # define variables in $cfg_ref from xml file

    my ($self, $file) = @_;

    my $xml = XML::LibXML->new( no_blanks => 1)->parse_file($file);
    
    my @nodes = $xml->findnodes(".//entry");
    if (! @nodes) {
	die "ERROR add_config_variables: no variable elements in file $file \n"; 
    }

    foreach my $node (@nodes) 
    {
	my $id = $node->getAttribute('id');
	foreach my $define_node ($node->childNodes()) 
	{
	    my $name = $define_node->nodeName();
	    my $value = $define_node->textContent();
	    $self->{$id}->{$name} = $value;
	}
	# now set the initial value to the default value - this can get overwritten
	if (! defined $self->{$id}->{'default_value'} ) {
	    die "ERROR add_config_variables: default_value must be set for $id \n";
	} else {
	    # At the beginning set the value to the default value
	    $self->{$id}->{'value'} = $self->{$id}->{'default_value'};
	}
    }
}

#-----------------------------------------------------------------------------------------------
sub set
{
    # Set requested value.
    # This routine handles errors by throwing exceptions.  It will report exactly what problem was
    # found in either the parameter name or requested value.
    # To avoid dealing with exceptions use the is_valid_name(), is_valid_value() methods to get a
    # true/false return before calling the set method.

    my ($self, $id, $value) = @_;

    # Check that the parameter name is in the configuration definition
    unless ($self->is_valid_name($id)) { 
	die "ERROR ConfigCase::set: $id is not a valid name \n";
    }

    # Get the type description hash for the variable and check that the type is valid
    # This method throws an exception when an error is encountered.
    my %type_ref = $self->_get_typedesc($id);
    validate_variable_value($id, $value, \%type_ref);


    # Check that the value is valid
    my $valid_values = $self->{$id}->{'valid_values'};
    if ( $valid_values ne "" ) {
	my $value = _clean($value);
	my $is_list_value = $self->{$id}->{'list'};
	is_valid_value($id, $value, $valid_values, $is_list_value) or die
	    "ERROR: value of $value is not a valid value for parameter $id: valid values are $valid_values\n";
    }
    # Add the new value to the object's internal data structure.
    $self->{$id}->{'value'} = $value;

    return 1;
}

#-----------------------------------------------------------------------------------------------
sub get
{
    # Return requested value.
    my ($self, $name) = @_;

    defined($self->{$name}) or die "ERROR ConfigCase.pm::get: unknown parameter name: $name\n";

    return $self->{$name}->{'value'};
}

#-----------------------------------------------------------------------------------------------
sub getresolved
{
    # returns the value set in name with all embeded parameters resolved.
    my($self,$name) = @_;

    my $val = $self->get($name);
    
    my @vars = grep(/\$([\w_]+)/,$val);
    my $v1 = $val;

    while($v1 =~ /\$([\w_]+)(.*)$/){
	print "v1: $v1\n";
	my $newvar=$1;
	$v1 = $2;
	if(self->is_valid_name($newvar)){
	    my $v2=$self->getresolved($newvar);
	    $val =~ s/\$$newvar/$v2/;
	}
    }
    return $val;
}

#-----------------------------------------------------------------------------------------------
sub get_var_type
{
    # Return 'type' attribute for requested variable
    my ($self, $name) = @_;

    return $self->{$name}->{'type'};
}

#-----------------------------------------------------------------------------------------------
sub get_valid_values
{
    # Return list of valid_values as an array for requested variable
    # To return without quotes use the 'noquotes'=>1 option.
    my ($self, $name, %opts) = @_;

    my $valid_values = $self->{$name}->{'valid_values'};
    my $type = $self->{$name}->{'type'};
    my @values = split( /,/, $valid_values );

    # if string type and NOT noquote option and have a list -- add quotes around values
    if ( ! defined($opts{'noquotes'}) || ! $opts{'noquotes'} ) {
       if ( $#values > -1 && ($type eq "char") ) {
          for( my $i=0; $i <= $#values; $i++ ) {
             $values[$i] = "'$values[$i]'";
          }
       }
    }
    return( @values );
}


#-----------------------------------------------------------------------------------------------
sub getAllResolved #TODO - move this out of here \n";
{
    # Parse all the xml files, and resolve every variable. 
    my $self = shift;

    # hash for all the parsers, and a hash for  all the config variables. 
    my %parsers;
    my %masterconfig;
    
    # Get all the env*.xml files into an array...
    my @xmlfiles = qw( env_build.xml env_case.xml env_mach_pes.xml env_run.xml);
    push(@xmlfiles, "env_test.xml") if(-e "./env_test.xml");
    push(@xmlfiles, "env_archive.xml") if(-e "./env_archive.xml");
    
    # Set up a new XML::LibXML parser for each xml file. 
    foreach my $basefile(@xmlfiles)
    {
	my $xml = XML::LibXML->new()->parse_file($basefile);
	$parsers{$basefile} = $xml;
    }
    
    # find all the variable nodes. 
    foreach my $basefile(@xmlfiles)
    {
	my $parser = $parsers{$basefile};	
	my @nodes = $parser->findnodes("//entry");
	foreach my $node(@nodes)
	{
	    my $id = $node->getAttribute('id');
	    my $value = $node->getAttribute('value');
	    # if the variable value has an unresolved variable, 
	    # we need to find it in whatever file it might be in. 
	    $value = _resolveValues($value, \%parsers);
	    $masterconfig{$id} = $value;
	}
    }
    return %masterconfig;
}

#-----------------------------------------------------------------------------------------------
sub is_valid_name
{
    # Return true if the requested name is contained in the configuration definition.

    my ($self, $name) = @_;
    return defined($self->{$name}) ? 1 : 0;
}

#-----------------------------------------------------------------------------------------------
sub is_char
{
    # Return true if the requested name is of character type
    my ($self, $name) = @_;

    if ( $self->_get_type($name) eq "char" ) {
        return( 1 );
    } else {
        return( 0 );
    }
}

#-----------------------------------------------------------------------------------------------
sub is_valid_value
{
    # Check if the input value is a valid value
    my ($id, $value, $valid_values, $is_list_value) = @_;

    # Check that a list value is not supplied when parameter takes a scalar value.
    unless ($is_list_value) {  # this conditional is satisfied when the list attribute is false, i.e., for scalars
	if ($value =~ /.*,.*/) {    
	    # the pattern matches when $value contains a comma, i.e., is a list
 	    die "Errorr is_valid_value; variable $id is a scalar but has a list value $value \n";
	}
   }

    # Check that the value is valid
    # if no valid values are specified, then $value is automatically valid
    if ( $valid_values ne "" ) {  
	if ($is_list_value) {
	    unless (list_value_ok($value, $valid_values)) { 
		die "ERROR is_valid_value: $id has value $value which is not a valid value \n";
	    }
	} else {
	    unless (value_ok($value, $valid_values)) { 
		die "ERROR is_valid_value: $id has value $value which is not a valid value \n";
	    }
	}

    }
    return 1;
}

#-----------------------------------------------------------------------------------------------
sub validate_variable_value
{
    # Validate that a given value matches the expected input type definition
    # Expected description of keys for the input type hash is:
    #      type           type description (char, logical, integer, or real)       (string)
    #      strlen         Length of string (if type char)                          (integer)
    #      validValues    Reference to array of valid values                       (string)
    #
    my ($var, $value, $type_ref) = @_;
    my $nm = "validate_variable_value";

    # Perl regular expressions to match Fortran namelist tokens.
    # Variable names.
    # % for derived types, () for arrays
    my $varmatch = "[A-Za-z_]{1,31}[A-Za-z0-9_]{0,30}[(0-9)%a-zA-Z_]*";

    # Integer data.
    my $valint = "[+-]?[0-9]+";
    my $valint_repeat = "${valint}\\*$valint";

    # Logical data.
    my $vallogical1 = "[Tt][Rr][Uu][Ee]";
    my $vallogical2 = "[Ff][Aa][Ll][Ss][Ee]";
    my $vallogical = "$vallogical1|$vallogical2";
    my $vallogical_repeat = "${valint}\\*$vallogical1|${valint}\\*$vallogical2";

    # Real data.
    # "_" are for f90 precision specification
    my $valreal1 = "[+-]?[0-9]*\\.[0-9]+[EedDqQ]?[0-9+-]*";
    my $valreal2 = "[+-]?[0-9]+\\.?[EedDqQ]?[0-9+-]*";
    my $valreal = "$valreal1|$valreal2";
    my $valreal_repeat = "${valint}\\*$valreal1|${valint}\\*$valreal2";

    # Match for all valid data-types: integer, real or logical
    # note: valreal MUST come before valint in this string to prevent integer portion of real 
    #       being separated from decimal portion
    my $valall = "$vallogical|$valreal|$valint";

    # Match for all valid data-types with repeater: integer, real, logical, or string data
    # note: valrepeat MUST come before valall in this string to prevent integer repeat specifier 
    #       being accepted alone as a value
    my $valrepeat = "$vallogical_repeat|$valreal_repeat|$valint_repeat";

    # Match for all valid data-types with or without numberic repeater at the lead
    my $valmatch = "$valrepeat|$valall";

    # Same as above when a match isn't required
    my $nrvalmatch = $valmatch. "||";

    # Ensure type hash has required variables
    if ( ref($type_ref) !~ /HASH/ ) {
	die "ERROR: in $nm : Input type is not a HASH reference.\n";
    }
    foreach my $item ( "type", "validValues", "strlen" ) {
	if ( ! exists($$type_ref{$item}) ) {
	    die "ERROR: in $nm: Variable name $item not defined in input type hash.\n";
	}
    }
    # If string check that less than defined string length
    my $str_len = 0;
    if ( $$type_ref{'type'} eq "char" ) {
	$str_len = $$type_ref{'strlen'};
	if ( length($value) > $str_len ) {
	    die "ERROR: in $nm Variable name $var " .
		"has a string element that is too long: $value\n";
	}
    }
    # If not string -- check that array size is smaller than definition
    my @values;
    if ( $str_len == 0 ) {
	@values = split( /,/, $value );
	# Now check that values are correct for the given type
	foreach my $i ( @values ) {
	    my $compare;
	    if (      $$type_ref{'type'} eq "logical" ) {
		$compare = $vallogical;
	    } elsif ( $$type_ref{'type'} eq "integer" ) {
		$compare = $valint;
	    } elsif ( $$type_ref{'type'} eq "real" ) {
		$compare = $valreal;
	    } else {
		die "ERROR: in $nm (package $pkg_nm): Type of variable name $var is " . 
		    "not a valid FORTRAN type (logical, integer, real, or char).\n";
	    }
	    if ( $i !~ /^\s*(${compare})$/ ) {
		die "ERROR: in $nm (package $pkg_nm): Variable name $var " .
		    "has a value ($i) that is not a valid type " . $$type_ref{'type'} . "\n";
	    }
	}
    }
}

#-----------------------------------------------------------------------------------------------
sub reset_setup
{
    # Reset the config object from the setup file
    my ($self, $setup_file, $setup_id) = @_;

    my $xml = XML::LibXML->new( no_blanks => 1)->parse_file($setup_file);

    foreach my $node ($xml->findnodes(".//entry")) {
	my $id    = $node->getAttribute('id');
	my $value = $node->getAttribute('value');

	if (defined($setup_id)) {
	    if ($id ne $setup_id) {$self->set($id, $value);}
	} else {
	    $self->set($id, $value);
	}
    } 
}

#-----------------------------------------------------------------------------------------------
sub write_file
{
    # Write an env_xxx.xml file (specified by $filename) in $caseroot
    my ($self, $output_xml_file, $definitions_file, $caseroot, $cimeroot, $input_xml_file) = @_;

    my $xml = XML::LibXML->new( no_blanks => 1)->parse_file($definitions_file);
    my @nodes = $xml->findnodes(".//entry[\@id=\"CASEFILE_DESCRIPTIONS\"]/default_value");
    my $casefiles_descriptions = $nodes[0]->textContent();
    $casefiles_descriptions =~ s/\$CIMEROOT/$cimeroot/;
    (-f $casefiles_descriptions) or die "ERROR _create_caseroot_files: file $casefiles_descriptions does not exist \n";

    if ( -f $output_xml_file ) { unlink( $output_xml_file ); }
    my $fh = IO::File->new($output_xml_file, '>' ) or die "can't open file: $output_xml_file\n";

    print $fh "<?xml version=\"1.0\"?> \n";
    print $fh "\n";
    print $fh "<config_definition> \n";
    print $fh "\n";

    _print_file_header($fh, $casefiles_descriptions, $output_xml_file); 

    if ($output_xml_file =~ /env_archive.xml/) {

	if (! $input_xml_file ) {
	    die "ERROR write_file: must specify input_xml_file as argument for writing out $output_xml_file \n";
	} else {
	    open CONFIG_ARCHIVE, $input_xml_file or die $!;
	    while (<CONFIG_ARCHIVE>) {
		chomp;
		print $fh "$_\n";
	    }
	    close (CONFIG_ARCHIVE);
	}

    } else {

	# determine all the possible group names for the target file 
	# not all of these will be contained in $cfg_ref
	my @groups = _get_group_names($casefiles_descriptions, $output_xml_file); 
	
	# now determine the unique set of groups that are in $cfg_ref
	my @groups_cfg;
	foreach my $id (keys %$self) {
	    my $id_group = $self->{$id}->{'group'};
	    foreach my $group (@groups) {
		if ( grep( /^$id_group$/, @groups ) ) {
		    if (@groups_cfg) {
			if ( grep( /^$group$/, @groups_cfg ) ) {
			    # do nothing
			} else {
			    # add it to the array groups_cfg
			    push (@groups_cfg, $group);
			}
		    } else {
			push (@groups_cfg, $group);
		    } 
		}
	    }
	}

	# now determine which groups will write out to the output xml file
	# these will be the particular subset of @groups that are also contained in @groups_cfg
	foreach my $group (@groups) {
	    if ( grep( /^$group$/, @groups_cfg ))  {
		$self->_write_xml($fh, $group);
	    }
	}
    }
	
    print $fh "\n";
    print $fh "</config_definition> \n";
}

#-----------------------------------------------------------------------------------------------
sub list_value_ok
{
    # Check that all input values ($values_in may be a comma separated list)
    # are contained in the comma separated list of valid values ($valid_values).
    # Return 1 (true) if all input values are valid, Otherwise return 0 (false).
    my ($values_in, $valid_values) = @_;

    my @values = split /,/, $values_in;
    my $num_vals = scalar(@values);
    my $values_ok = 0;

    foreach my $value (@values) {
	if (value_ok($value, $valid_values)) { ++$values_ok; }
    }
    ($num_vals == $values_ok) ? return 1 : return 0;
}

#-----------------------------------------------------------------------------------------------
sub value_ok
{
    # Check that the input value is contained in the comma separated list of
    # valid values ($valid_values).  Return 1 (true) if input value is valid,
    # Otherwise return 0 (false).
    my ($value, $valid_values) = @_;

    # If the valid value list is null, all values are valid.
    unless ($valid_values) { return 1; }

    my @expect = split /,/, $valid_values;

    $value =~ s/^\s+//;
    $value =~ s/\s+$//;
    foreach my $expect (@expect) {
	if ($value =~ /^$expect$/) { return 1; }
    }
    return 0;
}

#-----------------------------------------------------------------------------------------------
sub get_str_len
{
# Return 'str_len' attribute for requested variable

    my ($self, $name) = @_;
    my $lc_name = lc $name;

    return $self->{$lc_name}->{'str_len'};
}


#-----------------------------------------------------------------------------------------------
#                               Private routines
#-----------------------------------------------------------------------------------------------
sub _get_type
{
# Return 'type' attribute for requested variable

    my ($self, $name) = @_;

    return $self->{$name}->{'type'};
}

#-----------------------------------------------------------------------------------------------
sub _get_typedesc
#
# Return hash of description of data type read in from the file:
# Hash keys are:
#      type           type description (char, logical, integer, or real) (string)
#      strlen         Length of string (if type char)                          (integer)
#      validValues    Reference to array of valid values                 (string)
#
{
    my ($self, $name) = @_;
    my $nm = "_get_typedesc";

    my %datatype;
    my $type_def = $self->_get_type($name);
    my $lc_name = lc $name;
    if ($type_def =~ /^(char|logical|integer|real)/ ) {
	$datatype{'type'} = $1;
    } else {
	die "ERROR: in $nm (package $pkg_nm): datatype $type_def is NOT valid for $name \n";
    }
    if ( $datatype{'type'} eq "char" ) {
       if ($type_def =~ /^char\*([0-9]+)/ ) {
           $datatype{'strlen'} = $1;
       } else {
           $datatype{'strlen'} = 9999999;
       }
    } else {
       $datatype{'strlen'} = undef;
    }
    my @valid_values = $self->get_valid_values( $name );
    $datatype{'validValues'}  = \@valid_values;
    return( %datatype );
}

#-----------------------------------------------------------------------------------------------
sub _resolveValues
{
    # Recursively resolve the unresolved vars in an variable value.  
    # Check the value passed in, and if it still has an unresolved var, keep calling the function
    # until all pieces of the variable are resolved.  

    my $value = shift;
    my $parsers = shift;

    #print "in _resolveValues: value: $value\n";
    # We want to resolve $values from either tthe other xml files, or 
    # the value can come from the 
    if($value =~ /(\$[\w_]+)/)
    {
	#print "in _resolveValues: value: $value\n";
	my $unresolved = $1;
	
	#print "need to resolve: $unresolved\n";
	my $needed = $unresolved;
	$needed =~ s/\$//g;
	
	my $found = 0;
	foreach my $parser(values %$parsers)
	{
	    my @resolveplease = $parser->findnodes("//entry[\@id=\'$needed\']");
	    if(@resolveplease)
	    {
		$found = 1;
		foreach my $r(@resolveplease)
		{
		    my $rid = $r->getAttribute('id');
		    my $rvalue = $r->getAttribute('value');
		    $value =~ s/\$$needed/$rvalue/g;
		    #print "value after substitution: $value\n";
		}
	    }
	}
	# Check the environment if not found in the xml files. 
	if(!$found)
	{
	    if(exists $ENV{$needed})
	    {
		$found = 1;
		my $rvalue = $ENV{$needed};
		$value =~ s/\$$needed/$rvalue/g;
	    }
	}
	#if the value is not found in any of the xml files or in the environment, then
	# return undefined. 
	if(!$found)
	{
	    return undef;
	}
	_resolveValues($value, $parsers);
    }
    else
    {
	#print "returning $value\n";
	return $value;
    }
}

#-------------------------------------------------------------------------------
sub _get_group_names
{
    my ($headerfile, $filename) = @_;

    my $file = basename($filename);

    my $xml_nodes = XML::LibXML->new( no_blanks => 1)->parse_file($headerfile);
    my @group_nodes = $xml_nodes->findnodes(".//file[\@name=\"$file\"]/groups/group");
    my @groups;
    foreach my $group_node (@group_nodes) {
	my $group = $group_node->textContent();
	push (@groups, $group);
    }
    return (@groups);
}

#-------------------------------------------------------------------------------
sub _print_file_header
{
    my ($fh, $case_xmlfiles, $filename) = @_;

    my $file = basename($filename);

    my $xml = XML::LibXML->new( no_blanks => 1)->parse_file($case_xmlfiles);
    my @nodes = $xml->findnodes(".//file[\@name=\"$file\"]/header");
    my $text = $nodes[0]->textContent();
    print $fh "<header>";
    print $fh "$text \n";
    print $fh "</header> ";
}


#-----------------------------------------------------------------------------------------------
sub _write_xml
{
    # Output an xml file from $self
    my ($self, $fh, $group) = @_;

    # separate the groups with spaces
    print $fh "\n";
    
    foreach my $id (sort keys %$self) {
	if ($group eq $self->{$id}->{'group'}) {
	    $self->{$id}->{'value'} =~ s/'/&apos;/g;
	    $self->{$id}->{'value'} =~ s/\</&lt;/g;
	    $self->{$id}->{'value'} =~ s/\</&gt;/g;

	    print $fh "\n";
	    print $fh "<entry id=\"$id\"  value=\"$self->{$id}->{'value'}\" \n";   	    
	    print $fh "   type=\"$self->{$id}->{'type'}\" \n"; 
	    if ($self->{$id}->{'valid_values'} ne '') {
		print $fh "   valid_values=\"$self->{$id}->{'valid_values'}\" \n";
	    }
	    if ($self->{$id}->{'list'} ne '') {
		print $fh "   list=\"$self->{$id}->{'list'}\" \n";
	    }
	    my $desc = $self->{$id}->{'desc'};
	    $desc =~ s/\n//;
	    $desc =~ s/\n$//;
	    $desc =~ s/\r//;
	    $desc =~ s/^ *//;
	    $desc =~ s/ *$//g;
	    $desc =~ s/ *\n$//g;
	    chomp $desc;
	    print $fh "   desc=\"$desc\"/>\n";
	}
    }
}

#-------------------------------------------------------------------------------
sub _clean
{
    my ($name) = @_;
    $name =~ s/^\s+//; # strip any leading whitespace 
    $name =~ s/\s+$//; # strip any trailing whitespace
    return ($name);
}

#-----------------------------------------------------------------------------------------------
#                               Public routines to be deprecated
#-----------------------------------------------------------------------------------------------
sub write_docbook_master
{
    # Write the documentation on the configuration to an output README file.

    my $self = shift;
    my $filename = shift;   # filepath for output namelist

    my $fh;
    if ( -f $filename ) { unlink( $filename ); }
    $fh = IO::File->new($filename, '>' ) or die "can't open file: $filename\n";

    my $gid;

    if ($filename =~ "case") { 
        $gid = "case";
	print $fh "<table><title>env_case.xml variables</title>\n";
    } elsif($filename =~ "build") {
        $gid = "build";
	print $fh "<table><title>env_build.xml variables</title>\n";
    } elsif($filename =~ "mach_pes") {
        $gid = "mach_pes";
	print $fh "<table><title>env_mach_pes.xml variables</title>\n";
    } elsif($filename =~ "run") {
        $gid = "run";
	print $fh "<table><title>env_run.xml variables</title>\n";
    }
	print $fh "<tgroup cols=\"4\">\n";
	print $fh "<thead>\n";
	print $fh "<row> \n";
	print $fh "<entry>Name</entry>\n";
	print $fh "<entry>Type</entry>\n";
	print $fh "<entry>Default</entry>\n";
	print $fh "<entry>Description [Valid Values]</entry>\n";
	print $fh "</row> \n";
	print $fh "</thead>\n";
	print $fh "<tbody>\n";
    
    my @ids = keys %$self;
    foreach my $id (sort @ids) {

        my $desc = "";
        my $valid = "";
        my $value = "";
        my $type  = "";

        $desc = $self->{$id}->{'desc'};
  	$valid = $self->{$id}->{'valid_values'};
	$value = $self->{$id}->{'value'};
	$type  = $self->{$id}->{'type'};

        if ( ! defined($desc) ) { $desc = ""; }
        if ( ! defined($valid) ) { $valid = ""; }
        if ( ! defined($value) ) { $value = ""; }
        if ( ! defined($type) ) { $type = ""; }

	    if ( $self->{$id}->{'group'} =~ $gid ) {
		print $fh "<row> \n";
		print $fh "<entry>$id</entry>\n";
		print $fh "<entry>$type</entry>\n";
		print $fh "<entry>$value</entry>\n";
		if ($self->{$id}->{'valid_values'}) {
		    print $fh "<entry>$desc [$valid] </entry>\n";
		} else {
		    print $fh "<entry>$desc</entry>\n";
                }
		print $fh "</row>\n";
	    }	    
    }
    print $fh "</tbody>\n";
    print $fh "</tgroup>\n";
    print $fh "</table>\n";
}

#-------------------------------------------------------------------------------
1; # to make use or require happy
