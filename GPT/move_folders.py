#!/usr/bin/python

import os

for d in range(10,70,10):
    for r in range(2,6,1):
        print 'mv *'+str(d)+'dl_*'+str(r)+'rnk* youcook_synthetic_experiments/'+str(d)+'/'+str(r)+'/'
        os.system('mv *'+str(d)+'dl_*'+str(r)+'rnk* youcook_synthetic_experiments/'+str(d)+'/'+str(r)+'/')
