package ConfigTests;
my $pkg_nm = 'ConfigTests';

use strict;
use English;
use IO::File;
use XML::LibXML;
use Data::Dumper;
use ConfigCase;

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
  The perl module XML::LibXML is needed for XML parsing in the CESM script system.
  Please contact your local systems administrators or IT staff and have them install it for
  you, or install the module locally.  

END
    print "$warning\n";
    exit(1);
}

#-------------------------------------------------------------------------------
sub setTests
{
    # Set the parameters for the specified testname.  The
    # parameters are read from an input file, and if no testname matches are
    # found then issue error message.
    # This routine uses the configuration defined at the package level ($cfg_ref).

    my ($testfile, $testname, $cfg_ref) = @_;

    my $xmlparser = XML::LibXML->new( no_blanks => 1)->parse_file("$testfile");
    my @tests = $xmlparser->findnodes(".//test");
    my $found;
    foreach my $test (@tests) {
	my $name = $test->getAttribute('NAME');
	if ($testname eq $name) {
	    $found = 1;
	    last;
	}
    }
    # Die unless search was successful.
    unless ($found) { 
	print "set_test: no match for test $testname - possible testnames are \n";
	foreach my $test (@tests) {
	    my $name = $test->getAttribute('NAME');
	    my $desc = $test->getAttribute('DESC');
	    print " $name ($desc) \n" ;
	}
	die "set_test: exiting\n"; 
    }

    # Loop through all entry_ids of the $cfg_ref object and if the corresponding attribute
    # is defined in the test node, then reset the cfg_ref object to that value

    my @ids = keys %$cfg_ref;
    foreach my $id (sort @ids) {
	foreach my $test (@tests) {
	    foreach my $node ($test->childNodes()) {
		my $name = $node->nodeName();
		if ( ! $cfg_ref->is_valid_name($name) ) { 
		    die "set_test: invalid element $name in test $testname in file $testfile exiting\n"; 
		}
		if ($name eq $id) {
		    my $value = $node->textContent();
		    $cfg_ref->set($id, $value);
		}
	    }
	}
    }
}
#-------------------------------------------------------------------------------
sub listTests
{
    # Print the list of supported tests
    my ($test_file) = @_;

    my $parser = XML::LibXML->new( no_blanks => 1);
    my $xml = $parser->parse_file($test_file);

    print ("  \n");
    print ("  TESTS:  name (description) \n");

    foreach my $node ($xml->findnodes(".//test")) {
	my $name = $node->getAttribute('NAME');
	my $desc = $node->getAttribute('DESC');
	if (defined ($desc)) { 
	    print "    $name ($desc) \n";
	}
    }
}

#-----------------------------------------------------------------------------------------------
#                               Private routines
#-----------------------------------------------------------------------------------------------

1;
