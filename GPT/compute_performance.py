#!/usr/bin/python

import os
from multiprocessing import Pool

def process(args):
    print 'nice -n 20 ./organize_results_new.py '+' '.join(args)+' '
    #os.system('./organize_results_new.py '+' '.join(args)+' ')
    os.system('./calculate_performance.py '+' '.join(args[0:-1]) + ' -gci ' + args[-1])
    #os.system('./calculate_performance.py '+' '.join(args[0:-1]) + ' ' +  args[-1])

def main():
    number_of_processes = 10
    rootpath = 'youcook_experiments'
    dataset_name = 'youcook'
    window_sizes = ['1shots', '2shots','3shots','4shots']
    bond_types = ['support_bond','semantic_bond','temporal_bond']
    bond_weights = [1, 1.5, 2, 2.5, 3]

    tasks = []
    for type in bond_types:
        for weight in bond_weights:
            subpath = type + '_weights/' + str(weight)
            for window in window_sizes:
                input_path = rootpath + '/' + subpath
                args = (input_path, 'real', window, 'results', subpath, dataset_name)
                tasks.append(args)
                #process(args)

    pool = Pool(number_of_processes)
    pool.map(process, tasks)

if __name__ == '__main__':
    main()
