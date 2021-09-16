#!/usr/bin/env python
import os
import sys
import glob

compnames = ("intel", "cray", "gnu", "pgi", "ibm", "nag", "pgi-gpu")
for comp in compnames:
    with open(comp+".cmake") as fd:
        lines = fd.readlines()
    for _file in glob.iglob(comp+"_*.cmake"):
        with open(_file) as fl:
            theselines = fl.readlines()
        keepnew = False
        with open(_file+".new", "w") as fo:
            for line in theselines:
                if line in lines and not line.startswith('if') and not line.startswith("endif"):
                    keepnew = True
                    print("skipping line {}".format(line))
                else:
                    fo.write(line)
        if keepnew:
            os.remove(_file)
            os.rename(_file+".new", _file)
        else:
            os.remove(_file+".new")
