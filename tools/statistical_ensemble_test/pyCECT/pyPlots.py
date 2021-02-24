#!/usr/bin/env python

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

#change to input argument later
filename = 'savefile.nc'
test = 'hr_mpeO3_9ts'
ptest = ' ('+test+')'

ds = xr.open_dataset(filename)

test_size = ds.dims['test_size']
ens_size = ds.dims['ens_size']
nvars = ds.dims['nvars']

#get var list and names
vars = ds['vars'].values

#get test scores and means
t_scores = ds['scores'].values
t_std_gm = ds['std_gm'].values

#get ens scores distribution and ens means
ens_score_dist = ds['ens_sigma_scores'].values
ens_std_gm = ds['ens_std_gm'].values

all_outside99 = []
two_outside99 = []
one_outside99 = []
all_oneside_IQR = []

#go through each variables
for i, thisvar in enumerate(vars):
    #print i
    #print thisvar
    #ensemble distribution information
    p995 = np.percentile(ens_std_gm[i,:],99.5)
    p75 = np.percentile(ens_std_gm[i,:],75)
    p25 = np.percentile(ens_std_gm[i,:],25)
    p05 = np.percentile(ens_std_gm[i,:],0.5)
    #print p995
    
    isout_995 = 0
    isout_75 = 0
    isout_25 = 0
    #go through the test cases

    #outside of 995 or all on one side?
    for j in range(test_size):
        #print j
        thisval = t_std_gm[i,j]
        if thisval > p995 or thisval < p05:
            isout_995 = isout_995+1
        if thisval > p75:
            isout_75 = isout_75 + 1
        if thisval < p25:
            isout_25 = isout_25 + 1

    if isout_995 == 1:
        one_outside99.append(i)
    elif isout_995 == 2:
        two_outside99.append(i)
    elif isout_995 == 3:
        all_outside99.append(i)
    
    if isout_75 == 3 or isout_25 == 3:
        all_oneside_IQR.append(i)

num_one99 = len(one_outside99)
num_two99 = len(two_outside99)
num_all99 = len(all_outside99)
num_oneside = len(all_oneside_IQR)

c = set(one_outside99) | set(two_outside99) | set(all_outside99) | set(all_oneside_IQR)
uni = len(c)

print "total variables = ", nvars
print "one test outside 99th percentile = ", num_one99
print "two tests outside 99th percentile = ", num_two99
print "three (all) tests outside 99th percentile = ", num_all99
print "all tests on one side of IQR =  ", num_oneside
print "unique number of variables that fall into the above categories = ", uni

#now make plots
ens_list_array = []
test_points = []
flierprops = dict(marker='x', markerfacecolor='gray', markersize=1)
#all outside
if (num_all99 > 0):
    sf_name = 'all_out99_' + test + '.png'
    for i in  all_outside99:
        ens_list_array.append(ens_std_gm[i,:])
        test_points.append(t_std_gm[i,:])
    labels = vars[all_outside99]
    f = plt.figure()
    sns.boxplot(data=ens_list_array, flierprops=flierprops, whis=[0.5,99.5])
#    sns.boxplot(data=ens_list_array, fliersize= 2.0) 
    sns.stripplot(data = test_points, jitter = True, color="r", size=3, marker="D")
    plt.title('Variables with all (three) tests outside the 99th percentile'+ ptest)
    plt.ylabel('standardized global means')
    plt.xticks(range(num_all99), labels, fontsize=8,rotation='vertical')
    plt.subplots_adjust(bottom=0.2)
    plt.savefig(sf_name, bbox_inches='tight')
    f.clear()
    plt.close(f)

#two outside 
if (num_two99 > 0):
    sf_name = 'two_out99_' + test + '.png'
    ens_list_array = []
    test_points = []                                                                                                                          
    for i in  two_outside99:
        ens_list_array.append(ens_std_gm[i,:])
        test_points.append(t_std_gm[i,:])
    labels = vars[two_outside99]
    f = plt.figure()
    sns.boxplot(data=ens_list_array, flierprops=flierprops, whis=[0.5,99.5])
#    sns.boxplot(data=ens_list_array, fliersize= 2.0)
    sns.stripplot(data = test_points, jitter = True, color="r", size=3, marker="D")
    plt.title('Variables with two tests outside the 99th percentile' + ptest)
    plt.ylabel('standardized global means')
    plt.xticks(range(num_two99), labels, fontsize=8,rotation='vertical')
    plt.subplots_adjust(bottom=0.2)
    plt.savefig(sf_name, bbox_inches='tight')
    f.clear()
    plt.close(f)

#one outside    
if (num_one99 > 0):                                                                                                                               
    sf_name = 'one_out99_' + test + '.png'
    ens_list_array = []
    test_points = []
    for i in  one_outside99:
        ens_list_array.append(ens_std_gm[i,:])
        test_points.append(t_std_gm[i,:])
    labels = vars[one_outside99]
    f = plt.figure()
    sns.boxplot(data=ens_list_array, flierprops=flierprops, whis=[0.5,99.5])
#    sns.boxplot(data=ens_list_array, fliersize= 2.0)
    sns.stripplot(data = test_points, jitter = True, color="r", size=3, marker="D")
    plt.title('Variables with one test outside the 99th percentile' + ptest)
    plt.ylabel('standardized global means')
    plt.xticks(range(num_one99), labels, fontsize=8,rotation='vertical')
    plt.subplots_adjust(bottom=0.2)
    plt.savefig(sf_name, bbox_inches='tight')
    f.clear()
    plt.close(f)

#oneside
if (num_oneside > 0): 
    sf_name = 'oneside_IQR_' + test + '.png'
    ens_list_array = []
    test_points = []
    for i in  all_oneside_IQR:
        ens_list_array.append(ens_std_gm[i,:])
        test_points.append(t_std_gm[i,:])
    labels = vars[all_oneside_IQR]
    f = plt.figure()
    sns.boxplot(data=ens_list_array, flierprops=flierprops, whis=[0.5,99.5])
#    sns.boxplot(data=ens_list_array, fliersize= 2.0)
    sns.stripplot(data = test_points, jitter = True, color="r", size=3, marker="D")
    plt.title('Variables with all tests on one side of the IQR' + ptest)
    plt.ylabel('standardized global means')
    plt.xticks(range(num_oneside), labels, fontsize=8,rotation='vertical')
    plt.subplots_adjust(bottom=0.2)
    plt.savefig(sf_name, bbox_inches='tight')
    f.clear()
    plt.close(f)
