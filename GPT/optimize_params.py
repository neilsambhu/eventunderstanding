#!/home/students/fillipe/anaconda/bin/python

import os
from multiprocessing import Pool

def parse_performance_rate(performance_file):
    line = '0.0'
    for line in open(performance_file,'r'): pass
    return float(line.strip().split(':')[-1])

def run(cmd):
    os.system(cmd + ' > out'+str(os.getpid()))

def main():

    fold_number = 1
    number_of_segments = 1

    split_folder_name = 's'+str(fold_number)
    segment_test_files_path = str(number_of_segments)+'seg'

    params = {'support_weights': [x/10.0 for x in range(5,35,5)],
              'ontological_weights': [x/10.0 for x in range(5,35,5)],
              'feature_thresholds': [x/10. for x in range(1,10,1)]}

#    pool = Pool(4)

#    tasks = []
#    for w0 in params['ontological_weights']:
#        for w1 in params['support_weights']:
#            # create bond weights file here
#            bond_weights_filename = 'bond_weights_ow'+repr(w0)+'_sw'+repr(w1)+'.txt'
#            bond_weights_file = open(bond_weights_filename,'w')
#            bond_weights_file.write('semantic '+repr(w0)+'\n')
#            bond_weights_file.write('support '+repr(w1)+'\n')
#            bond_weights_file.write('temporal '+repr(1.)+'\n')
#            bond_weights_file.close()
#            # run experiments for different feature thresholds
#            for t0 in params['feature_thresholds']:
#                experiment_name = 'ow' + str(w0) + '_sw' + str(w1) + '_ft' + str(t0)
#                cmd = 'nice -n 20 ./mp_real.py unit_test_features/'+split_folder_name+'/'+segment_test_files_path+' ' \
#                      + split_folder_name + '_' + segment_test_files_path + ' ' + experiment_name + ' regular ' + \
#                      bond_weights_filename + ' ' + str(t0)
#                tasks.append(cmd)
#    # execute tasks here
#    pool.map(run,tasks)

    # compute performance here
    annotations_path = '/home/students/fillipe/Breakfast_Final/lab_raw'
    results_root_path = '/home/students/fillipe/ICCV2015'
    performance_filename = 'grid_performance_file_'+split_folder_name+'_'+segment_test_files_path+'.txt'
    os.system('touch '+performance_filename)
    performance_file = open(performance_filename,'a')
    for w0 in params['ontological_weights']:
        for w1 in params['support_weights']:
            for t0 in params['feature_thresholds']:
                experiment_name = 'ow' + str(w0) + '_sw' + str(w1) + '_ft' + str(t0)
                results_path = results_root_path + '/' + experiment_name + '/' + split_folder_name + '_' + \
                               segment_test_files_path + '_results'
                cmd = 'nice -n 20 ./measure_performance.py ' + annotations_path + ' ' + results_path +\
                      ' > performance_tmp.txt'
                print cmd
                os.system(cmd)
                score = repr(parse_performance_rate('performance_tmp.txt'))
                print 'Performance Rate: ',score
                performance_file.write(score+' ')
            performance_file.write('\n')
        performance_file.write('\n')
    performance_file.close()

if __name__ == '__main__':
    main()
