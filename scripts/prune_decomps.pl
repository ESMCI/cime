#!/usr/bin/env perl
use strict;
use warnings;

use Getopt::Long;

my $rundir="";
my $exe="";
my $nargs = 0;
my $verbose = 0;

# Remove duplicate decomposition files in "dirname"
sub rem_dup_decomp_files
{
    my($dirname) = @_;
    # Find files in current directory that are
    # named *piodecomp* - these are the pio 
    # decomposition files
    opendir(F,$dirname);
    my @decompfiles = grep(/^piodecomp/,readdir(F));
    closedir(F);
    my $rmfile=0;
    # Compare the decomposition files to find
    # duplicates - and delete the dups
    for(my $i=0; $i< $#decompfiles; $i++){
        my $file  = $decompfiles[$i];
        my $fsize = -s $file;
        for(my $j=$i+1;$j<$#decompfiles;$j++){
            my $nfile = $decompfiles[$j];
            my $f2size = -s $nfile;
            if($fsize == $f2size){
                open(F1,$file);
                my @file1 = <F1>;
                open(F2,$nfile);
                my @file2 = <F2>;
                foreach my $line (@file1){
                    my $nline = shift (@file2);
                    # Ignore stack traces when comparing files
                    # The stack traces start with a line containing
                    # "Obtained" 
                    # Also, stack trace is the last line being
                    # compared
                    if($line =~ /Obtained/){
                        print "Files $file and $nfile are the same\n";
                        $rmfile=1;
                    }
                    next if($line == $nline);
                    last;
                }
                close(F1);
                close(F2);
                unlink($nfile) if ($rmfile==1);
            }
        }
    }
}

# Decode the stack traces in the pio decomposition files
sub decode_stack_traces
{
    # dirname => Directory that contains decomp files
    # exe => executable (including path) that generated
    #         the decomposition files
    my($dirname, $exe) = @_;
    # Decode/Translate the stack trace
    opendir(F,$dirname);
    my @decompfiles = grep(/^piodecomp/,readdir(F));
    closedir(F);
    for(my $i=0; $i<= $#decompfiles; $i++){
        my $file = $decompfiles[$i];
        open(F1,$file);
        my @file1 = <F1>;
        close(F1);
        open(F1,">$file");
        foreach(@file1){
            # Find stack addresses in the file and use
            # addrline to translate/decode the filenames and
            # line numbers from it
            if(/\[(.*)\]/){
                my $decode = `addr2line -e $exe $1`;
                print F1 "$decode\n";
                print  "$decode\n";
            }else{
                print F1 $_;
            }
        }
        close(F1);
    }
}

sub print_usage_and_exit()
{
    print "\nUsage :\n./prune_decomps.pl --decomp-prune-dir=<PRUNE_DECOMP_DIR> \n";
    print "\tOR\n";
    print "./prune_decomps.pl <PRUNE_DECOMP_DIR> \n";
    print "The above commands can be used to remove duplicate decomposition\n";
    print "files in <PRUNE_DECOMP_DIR> \n";
    print "Available options : \n";
    print "\t--decomp-prune-dir : Directory that contains the decomp files to be pruned\n";
    print "\t--exe      : Executable that generated the decompositions \n";
    print "\t--verbose  : Verbose debug output\n";
    exit;
}

# Main program

# Read input args
GetOptions(
    "decomp-prune-dir=s"    => \$rundir,
    "exe=s"             => \$exe,
    "verbose"               => \$verbose
);

$nargs = @ARGV;

if($rundir eq ""){
    $rundir = shift;
    if($rundir eq ""){
        &print_usage_and_exit();
    }
}
if($verbose){ print "Removing duplicate decomposition files from : \"", $rundir, "\"\n"; }
&rem_dup_decomp_files($rundir);

if($exe ne ""){
    if($verbose){ print "Decoding stack traces for decomposition files from : \"", $rundir, "\"\n"; }
    &decode_stack_traces($rundir, $exe);
}

    
