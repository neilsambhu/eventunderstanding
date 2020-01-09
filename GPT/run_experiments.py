#!/usr/bin/python

import sys
import os
from multiprocessing import Pool

def local_help():
    print 'usage: ./summarize_all.py experiment_type experiments inference_versions rank_index ' \
              '[dataset_name|degradation rank]'
    exit(1)

def change_bond_weight_file(bond_type, weight):
    file = open('youcook_bond_weights_ptf.txt.bck','r')

    bond_weight_filename = 'youcook_bond_weights_ptf_' + bond_type + str(weight) + '.txt'
    output = open(bond_weight_filename, 'w')

    for line in file:
        data = line.strip().split()
        if bond_type == 'support_bond':
            if data[0] == 'hof' or data[0] == 'hog':
                output.write(data[0] + ' ' + str(weight)+'\n')
            else:
                output.write(' '.join(data) + '\n')
        elif bond_type == 'semantic_bond':
            if data[0] != 'hof' and data[0] != 'hog':
                output.write(data[0] + ' ' + str(weight)+'\n')
            else:
                output.write(' '.join(data) + '\n')
        elif bond_type == 'temporal_bond':
            if data[0] == 'actions':
                output.write(data[0] + ' ' + str(weight) + '\n')
            else:
                output.write(' '.join(data) + '\n')
    output.close()
    file.close()

    return bond_weight_filename

def process(args):
    os.system('nice -n 20 ./mp_real.py ' + ' '.join(args) + ' > out')

def main():
    dataset_name = 'youcook'
    test_files_path = 'multiple_shot_test'
    window_sizes = ['1shots']
    #window_sizes = ['2shots','3shots','4shots']
    inference_versions = ['notemporalbonds','temporalbonds']
    output_path = 'youcook_experiments'
    number_of_processes = 8

    tasks = []

    for window in window_sizes:
        for bond_type in ['support_bond','semantic_bond','temporal_bond']:
            for weight in [1, 1.5, 2, 2.5, 3]:
                #if weight in [1.5, 3] and bond_type == 'support_bond':
                #    continue

                if weight == 1 and bond_type != 'support_bond':
                    continue

                bond_weight_filename = change_bond_weight_file(bond_type,weight)
                for approach in inference_versions:
                    if approach == 'notemporalbonds':
                        options = ' -ntb -ndi'
                    elif approach == 'temporalbonds':
                        options = ' -tb -ndi'

                    tasks.append( (test_files_path+'/'+window,
                              dataset_name + '_' + window + '_' + approach,
                              output_path + '/' + bond_type + '_weights/' + str(weight), 'regular',
                              bond_weight_filename, options))

    pool = Pool(number_of_processes)
    pool.map(process, tasks)

if __name__ == '__main__':
    main()
