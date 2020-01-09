#!/usr/bin/python

import os
from multiprocessing import Pool

def process(arg):
    os.system(arg)

def main():
    func = 'performance_rank'
    #func = 'performance_weight' 
    #func = 'performance_rankdropping'
    #func = 'synthetic_performance_degradation'
    tasks = []
    for expname in ['1shots','2shots','3shots','4shots']:
        cmd = '/apps/matlab/r2014b/bin/matlab -nodesktop -r "'+func+'(\'youcook_experiments\',\''+expname+'\');quit;"'
        os.system(cmd)
    
    #pool = Pool(4)
    #pool.map(process,tasks)

if __name__ == '__main__':
    main()
