package ConfigPes;
my $pkg_nm = 'ConfigPes';

use strict;
use English;
use IO::File;
use XML::LibXML;
use Data::Dumper;
use ConfigCase;
use ConfigCESM;

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

#-----------------------------------------------------------------------------------------------
sub setPes {

    # Set the parameters for the pe layout.    

    my($pesize_opts, $compset_name, $mach, $cimeroot, $primary_component, $opts_ref, $cfg_ref) = @_;

    if (defined $$opts_ref{'pes_file'}) {

	# Reset the pes if a pes file is specified
	my $pes_file = $$opts_ref{'pes_file'};
	(-f "$pes_file")  or  die "** Cannot find pes_file \"$pes_file\" ***\n";
	$cfg_ref->reset_setup("$pes_file");    

    } else {

	if ($pesize_opts =~ m!^([0-9]+)D?$!) {

	    my $ntasks = $1;
	    my $nthrds = 1;
	    my $rootpe =  0;
	    _setPESmatch1($pesize_opts, $ntasks, $nthrds, $rootpe, $cfg_ref);

	} elsif ($pesize_opts =~ m!^([0-9]+)x([0-9]+)D?$!) {

	    my $ntasks = $1;
	    my $nthrds = $2;
	    my $rootpe =  0;
	    _setPESmatch2($pesize_opts, $ntasks, $nthrds, $rootpe, $cfg_ref);

	} else {

	    # Determine pes setup files
	    my $pes_file = _setPesSetupFile($cimeroot, $primary_component);

	    # Determine target grid
	    my $target_grid = ConfigCESM::setTargetGridMatch($primary_component, $cfg_ref );

	    _setPESsettings($pes_file, $mach, $target_grid, $compset_name, $pesize_opts, $cfg_ref);
	    _setPIOsettings($cimeroot, $mach, $cfg_ref);

	}
    }

}

#-----------------------------------------------------------------------------------------------
#                               Private routines
#-----------------------------------------------------------------------------------------------
sub _setPesSetupFile
{
    my ($cimeroot, $primary_component) = @_;

    my $pes_file; 

    if ($primary_component eq 'drv') {
	$pes_file = "$cimeroot/driver_cpl/cimeconfig/pelayouts.xml";
    } else {
	# TODO - this will need to be changed to be $cimeroot/../components when this is checked in
	$pes_file = "$cimeroot/scripts/cimeconfig/components/$primary_component/cimeconfig/pelayouts.xml"; 
    }
    (-f $pes_file) or  die "** Cannot find pes layout file $pes_file file \n";

    return ($pes_file);
}

#-------------------------------------------------------------------------------
sub _setPESmatch1
{
    my ($pesize_opts, $cfg_ref) = @_; 

    my $ntasks = $1;
    my $nthrds = 1;
    my $root = 0;

    foreach my $comp ("ATM", "LND", "ICE", "OCN", "GLC", "WAV", "ROF", "CPL" ) {
	$cfg_ref->set("NTASKS_$comp") = $ntasks; 
	$cfg_ref->set("NTHRDS_$comp") = $nthrds; 
    }

    my $root;
    if ($pesize_opts =~ m!^([0-9]+)D$!) {
	$root = 0          ; $cfg_ref->set('ROOTPE_ATM') = $root;
	$root = 1 * $ntasks; $cfg_ref->set('ROOTPE_LND') = $root;
	$root = 2 * $ntasks; $cfg_ref->set('ROOTPE_OCN') = $root;
	$root = 3 * $ntasks; $cfg_ref->set('ROOTPE_ICE') = $root;
	$root = 4 * $ntasks; $cfg_ref->set('ROOTPE_GLC') = $root;
	$root = 5 * $ntasks; $cfg_ref->set('ROOTPE_WAV') = $root;
	$root = 6 * $ntasks; $cfg_ref->set('ROOTPE_ROF') = $root;
	$root = 7 * $ntasks; $cfg_ref->set('ROOTPE_CPL') = $root;
    }

}

#-------------------------------------------------------------------------------
sub _setPESmatch2
{
    my ($pesize_opts, $ntasks, $nthrds, $rootpe, $cfg_ref) = @_; 

    foreach my $comp ("ATM", "LND", "ICE", "OCN", "GLC", "WAV", "ROF", "CPL") {
	$cfg_ref->set("NTASKS_$comp") = $ntasks; 
	$cfg_ref->set("NTHRDS_$comp") = $nthrds; 
    }
    
    my $root;
    if ($pesize_opts =~ m!^([0-9]+)x([0-9]+)D$!) {
	$root = 0          ; $cfg_ref->set('ROOTPE_ATM') = $root;
	$root = 1 * $ntasks; $cfg_ref->set('ROOTPE_LND') = $root;
	$root = 2 * $ntasks; $cfg_ref->set('ROOTPE_OCN') = $root;
	$root = 3 * $ntasks; $cfg_ref->set('ROOTPE_ICE') = $root;
	$root = 4 * $ntasks; $cfg_ref->set('ROOTPE_GLC') = $root;
	$root = 5 * $ntasks; $cfg_ref->set('ROOTPE_WAV') = $root;
	$root = 6 * $ntasks; $cfg_ref->set('ROOTPE_ROF') = $root;
	$root = 7 * $ntasks; $cfg_ref->set('ROOTPE_CPL') = $root;
    }
}    

#-------------------------------------------------------------------------------
sub _setPIOsettings
{
    # Set pio settings from config_pio.xml file

    my ($cimeroot, $mach, $cfg_ref) = @_; 

    my %pio_settings;

    # Initialize pio_settings
    $pio_settings{'ATM_PIO_TYPENAME'} = 'nothing';
    $pio_settings{'LND_PIO_TYPENAME'} = 'nothing';
    $pio_settings{'ICE_PIO_TYPENAME'} = 'nothing';
    $pio_settings{'OCN_PIO_TYPENAME'} = 'nothing';
    $pio_settings{'CPL_PIO_TYPENAME'} = 'nothing';
    $pio_settings{'GLC_PIO_TYPENAME'} = 'nothing';
    $pio_settings{'ROF_PIO_TYPENAME'} = 'nothing';
    $pio_settings{'WAV_PIO_TYPENAME'} = 'nothing';

    $pio_settings{'PIO_NUMTASKS'}    = -1;
    $pio_settings{'PIO_STRIDE'}	    = -1; 
    $pio_settings{'PIO_ROOT'}	    =  1;
    $pio_settings{'PIO_DEBUG_LEVEL'} =  0;
    $pio_settings{'PIO_TYPENAME'}    = 'netcdf';
    $pio_settings{'PIO_BUFFER_SIZE_LIMIT'} = -1;

    $pio_settings{'ATM_PIO_NUMTASKS'} = -99; 
    $pio_settings{'LND_PIO_NUMTASKS'} = -99; 
    $pio_settings{'ICE_PIO_NUMTASKS'} = -99; 
    $pio_settings{'OCN_PIO_NUMTASKS'} = -99; 
    $pio_settings{'CPL_PIO_NUMTASKS'} = -99; 
    $pio_settings{'GLC_PIO_NUMTASKS'} = -99; 
    $pio_settings{'ROF_PIO_NUMTASKS'} = -99; 
    $pio_settings{'WAV_PIO_NUMTASKS'} = -99; 

    $pio_settings{'ATM_PIO_STRIDE'}   = -99;
    $pio_settings{'LND_PIO_STRIDE'}   = -99;
    $pio_settings{'ICE_PIO_STRIDE'}   = -99;
    $pio_settings{'OCN_PIO_STRIDE'}   = -99;
    $pio_settings{'CPL_PIO_STRIDE'}   = -99;
    $pio_settings{'GLC_PIO_STRIDE'}   = -99;
    $pio_settings{'ROF_PIO_STRIDE'}   = -99;
    $pio_settings{'WAV_PIO_STRIDE'}   = -99;

    $pio_settings{'ATM_PIO_ROOT'}     = -99;
    $pio_settings{'LND_PIO_ROOT'}     = -99;
    $pio_settings{'ICE_PIO_ROOT'}     = -99;
    $pio_settings{'OCN_PIO_ROOT'}     =   0;
    $pio_settings{'CPL_PIO_ROOT'}     = -99;
    $pio_settings{'GLC_PIO_ROOT'}     = -99;
    $pio_settings{'ROF_PIO_ROOT'}     = -99;
    $pio_settings{'WAV_PIO_ROOT'}     = -99;

    # Read xml file
    my $parser = XML::LibXML->new( no_blanks => 1);
    my $cimeroot = $cfg_ref->get('CIMEROOT');
    my $file = $cfg_ref->get('DEFINITIONS_PIO_FILE');
    $file =~ s/\$CIMEROOT/$cimeroot/;

    my $grid = $cfg_ref->get('GRID');
    my $xmlparser = $parser->parse_file("$file");

    # Set pio settings to the default values
    my @pio_nodes = $xmlparser->findnodes(".//pio/mach[\@name=\"any\"]");
    foreach my $pio_node (@pio_nodes) {
	my @children = $pio_node->childNodes();
	foreach my $child (@children) {
	    my $name  = uc $child->nodeName(); 
	    my $value =    $child->textContent();
	    $pio_settings{$name}  = $value;
	}
    }
    
    # Overwrite default pio settings with supported machine settings
    my @pio_nodes = $xmlparser->findnodes(".//pio/mach[\@name=\"$mach\"]");
    foreach my $pio_node (@pio_nodes) {
	my @children = $pio_node->childNodes();
	foreach my $child (@children) {
	    my $name  = uc $child->nodeName(); 
	    my $grid_attr = $child->getAttribute('grid');
	    my $value;
	    if ($grid_attr) {
		if ($grid =~ /$grid_attr/) {
		    $value = $child->textContent();
		}
	    } else {
		$value = $child->textContent();
	    }
	    $pio_settings{$name}  = $value;
	}
    }

    foreach my $comp ("ATM", "LND", "ICE", "OCN", "GLC", "WAV", "ROF", "CPL") {

	my $name  = "${comp}" . "_PIO_NUMTASKS";
	my $value = $pio_settings{$name};
	$cfg_ref->set($name, $value);

	my $name = "${comp}" . "_PIO_STRIDE";
	my $value = $pio_settings{$name};
	$cfg_ref->set($name , $value);

	my $name = "${comp}" . "_PIO_ROOT";
	my $value = $pio_settings{$name};
	$cfg_ref->set($name, $value);

	my $name = "${comp}" . "_PIO_TYPENAME";
	my $value = $pio_settings{$name};
	$cfg_ref->set($name, $value );
    }
    $cfg_ref->set('PIO_TYPENAME'	  , $pio_settings{'PIO_TYPENAME'});
    $cfg_ref->set('PIO_BUFFER_SIZE_LIMIT' , $pio_settings{'PIO_BUFFER_SIZE_LIMIT'});
    $cfg_ref->set('PIO_NUMTASKS'	  , $pio_settings{'PIO_NUMTASKS'});
    $cfg_ref->set('PIO_STRIDE'	          , $pio_settings{'PIO_STRIDE'});
    $cfg_ref->set('PIO_ROOT'	          , $pio_settings{'PIO_ROOT'});
    $cfg_ref->set('PIO_DEBUG_LEVEL'	  , $pio_settings{'PIO_DEBUG_LEVEL'});
    $cfg_ref->set('PES_LEVEL'	          , 0);


}    
#-------------------------------------------------------------------------------
sub _setPESsettings
{
    # Read xml file and obtain NTASKS, NTHRDS, ROOTPE and NINST for each component
    my ($pes_file, $mach, $target_grid, $compset_name, $pesize_opts, $cfg_ref) = @_; 

    # temporary hash
    my %decomp;
    $decomp{'NTASKS_ATM'} = 16;
    $decomp{'NTASKS_LND'} = 16;
    $decomp{'NTASKS_ICE'} = 16;
    $decomp{'NTASKS_OCN'} = 16;
    $decomp{'NTASKS_ROF'} = 16;
    $decomp{'NTASKS_GLC'} = 16;
    $decomp{'NTASKS_WAV'} = 16;
    $decomp{'NTASKS_CPL'} = 16;

    $decomp{'NTHRDS_ATM'} = 1;
    $decomp{'NTHRDS_LND'} = 1;
    $decomp{'NTHRDS_ICE'} = 1;
    $decomp{'NTHRDS_OCN'} = 1;
    $decomp{'NTHRDS_ROF'} = 1;
    $decomp{'NTHRDS_GLC'} = 1;
    $decomp{'NTHRDS_WAV'} = 1;
    $decomp{'NTHRDS_CPL'} = 1;

    $decomp{'ROOTPE_ATM'} = 0;
    $decomp{'ROOTPE_LND'} = 0;
    $decomp{'ROOTPE_ICE'} = 0;
    $decomp{'ROOTPE_OCN'} = 0;
    $decomp{'ROOTPE_ROF'} = 0;
    $decomp{'ROOTPE_GLC'} = 0;
    $decomp{'ROOTPE_WAV'} = 0;
    $decomp{'ROOTPE_CPL'} = 0;

    #---------------------------------------------------
    # number of instances (always 1)
    #---------------------------------------------------
    
    my $parser = XML::LibXML->new( no_blanks => 1);
    my $xmlparser = $parser->parse_file($pes_file);

    my @pes_ninst  = $xmlparser->findnodes("./config_pes/pes_layout/pes/grid[\@name=\'any\']/mach[\@name=\'any\']/pes/ninst/*");
    foreach my $ninst (@pes_ninst) {
	my $name  = uc $ninst->nodeName(); 
	my $value =    $ninst->textContent();
	$cfg_ref->set($name, $value);
    }
    
    # --------------------------------------
    # look for target_grid / target_machine
    # --------------------------------------

    # Determine if there are any settings for target grid AND target_machine
    # If not, look for match for target_grid and 'any' machine
    # If not, look for match for 'any' grid and target_machine
    # If not, look for match for 'any' grid and 'any' machine
    
    my $mach_set = $mach; 
    my $grid_set = $target_grid;
    
    my @pes = $xmlparser->findnodes("./config_pes/pes_layout/grid[\@name=\"$grid_set\"]/mach[contains(\@name,\"$mach_set\")]/pes");
    if (! @pes) 
    {
	$mach_set = 'any';
	$grid_set = $target_grid;
	@pes = $xmlparser->findnodes("./config_pes/pes_layout/pes/grid[\@name=\"$grid_set\"]/mach[contains(\@name,\"$mach_set\")]/pes");
	if (! @pes) 
	{
	    $mach_set = $mach;
	    $grid_set = 'any';
	    @pes = $xmlparser->findnodes("./config_pes/pes_layout/pes/grid[\@name=\"$grid_set\"]/mach[contains(\@name,\"$mach_set\")]/pes");
	    if (! @pes) 
	    {
		$mach_set = 'any';
		$grid_set = $target_grid;
		@pes = $xmlparser->findnodes("./config_pes/pes_layout/pes/grid[\@name=\"$grid_set\"]/mach[contains(\@name,\"$mach_set\")]/pes");
		if (! @pes) 
		{
		    $mach_set = 'any';
		    $grid_set = 'any';
		    @pes = $xmlparser->findnodes("./config_pes/pes_layout/pes/grid[\@name=\"$grid_set\"]/mach[contains(\@name,\"$mach_set\")]/pes");
		    if (! @pes) 
		    {		    
			die "ERROR: no match found in $pes_file \n";
		    }
		}
	    }
	}
    }
    
    my @pes        = $xmlparser->findnodes("./config_pes/pes_layout/grid[\@name=\"$grid_set\"]/mach[contains(\@name,\"$mach_set\")]/pes");
    my @pes_ntasks = $xmlparser->findnodes("./config_pes/pes_layout/grid[\@name=\"$grid_set\"]/mach[contains(\@name,\"$mach_set\")]/pes/ntasks");
    my @pes_nthrds = $xmlparser->findnodes("./config_pes/pes_layout/grid[\@name=\"$grid_set\"]/mach[contains(\@name,\"$mach_set\")]/pes/nthrds");
    my @pes_rootpe = $xmlparser->findnodes("./config_pes/pes_layout/grid[\@name=\"$grid_set\"]/mach[contains(\@name,\"$mach_set\")]/pes/rootpe");
    
    # Loop over nodes that contain attributes for the target / target machine combination
    # examine the attributes of each node to determine the "best fit"
    # keep track of the number of attributes that match the configuration
    
    my @fit = ();
  ELEMENT: for (my $i = 0; $i <= $#pes; $i++) {
      my $pes_node = $pes[$i];
      my $matches = 0;
      
      # Loop over all attributes for the target element
      my @attributes = $pes_node->attributes();
      foreach my $attribute (@attributes) {
	  my $attribute_name  = $attribute->getName();
	  my $attribute_value = $attribute->getValue();
	  
	  $attribute_value =~ s/^\s+//;
	  $attribute_value =~ s/\s+$//;
	  $pesize_opts    =~ s/^\s+//;
	  $pesize_opts    =~ s/\s+$//;
	  
	  if ($attribute_name =~ m/compset/ ) {
	      if ($attribute_name =~ m/compset/ && $compset_name =~ m/$attribute_value/) {
		  $matches++;
	      } elsif  ($attribute_name =~ m/pesize/ && $pesize_opts =~ m/$attribute_value/)  {
		  $matches++;
	      } else {
		  $fit[$i] = -1;
		  next ELEMENT;
	      }
	  } # Finished attribute checks
      } # Finished loop over attributes
      
      # At this point the attribute checking has been successful.  Record the matches.
      $fit[$i] = $matches;
      
  } # Finished loop over nodes
    
    # All nodes have been examined.  Return the value from the best fit.  That's the 
    # index of the max value of @fit.  In case of a tie it's the first one found.
    if ( $#pes > -1) {
	my $max_val = $fit[0];
	my $max_idx = 0;
	for (my $i = 1; $i <= $#pes; $i++) {
	    if ($fit[$i] > $max_val) {
		$max_val = $fit[$i];
		$max_idx = $i;
	    }
	}
	
	# If "best fit" is $max_val = -1, then no match was found.
	my @pes_list;
	if ($max_val >= 0) {
	    @pes_list = ($pes_ntasks[$max_idx], $pes_nthrds[$max_idx], $pes_rootpe[$max_idx]);
	} else {
	    @pes_list = (@pes_ntasks, @pes_nthrds, @pes_rootpe);
	}
	foreach my $pes (@pes_list) {
	    my @children = $pes ->childNodes();
	    foreach my $child (@children) {
		my $name  = uc $child->nodeName(); 
		my $value =    $child->textContent();
		$decomp{$name}  = $value;
	    }
	}
    }
    
    # --------------------------------------
    # override settings
    # --------------------------------------
    
    my $xmlparser = $parser->parse_file($pes_file);
    foreach my $node_grid ($xmlparser->findnodes("./config_pes/pes_override/grid")) 
    {
	my $gridname = $node_grid->getAttribute('name');
	if (($gridname eq 'any') || ($gridname =~ /$grid_set/ )) 
	{
	    foreach my $node_mach ($node_grid->findnodes("./mach")) 
	    {
		my $machname = $node_mach->getAttribute('name');
		foreach my $node_pes ($node_mach->findnodes("./pes")) 
		{
		    my $pesize  = $node_pes->getAttribute('pesize');
		    my $compset = $node_pes->getAttribute('compset');
		    if (($pesize eq 'any' && $compset eq 'any') ||
			($pesize eq 'any' && $compset_name =~ /$compset/)) 
		    {
			foreach my $pes ($node_pes->findnodes("./ntasks"), 
					 $node_pes->findnodes("./nthrds"), 
					 $node_pes->findnodes("./rootpe")) {
			    my @children = $pes ->childNodes();
			    foreach my $child (@children) {
				my $name  = uc $child->nodeName(); 
				my $value =    $child->textContent();
				$decomp{$name}  = $value;
			    }
			}
		    }
		}
	    }
	}
    }
    
    foreach my $comp ("ATM", "LND", "ICE", "OCN", "GLC", "WAV", "ROF", "CPL") {
	my $ntasks = _clean($decomp{"NTASKS_$comp"});
	my $nthrds = _clean($decomp{"NTHRDS_$comp"});
	my $rootpe = _clean($decomp{"ROOTPE_$comp"});

	$cfg_ref->set("NTASKS_$comp" , $ntasks);
	$cfg_ref->set("NTHRDS_$comp" , $nthrds);
	$cfg_ref->set("ROOTPE_$comp" , $rootpe);
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

1;



