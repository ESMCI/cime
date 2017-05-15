#!/usr/bin/perl
use strict;

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
    my($dirname) = @_;
    # Decode/Translate the stack trace for CESM runs
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
                my $decode = `addr2line -e ../bld/cesm.exe $1`;
                print F1 "$decode\n";
                print  "$decode\n";
            }else{
                print F1 $_;
            }
        }
        close(F1);
    }
}

# Main program
my $rundir = shift;
&rem_dup_decomp_files($rundir);
&decode_stack_traces($rundir);

    
