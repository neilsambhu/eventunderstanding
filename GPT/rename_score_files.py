#!/usr/bin/python

import os
import glob

score_files = glob.glob('*.scores')

for file in score_files:
    os.system('mv '+file+' '+'_'.join(file.split('_')[1:]))
    

