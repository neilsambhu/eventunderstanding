#!/usr/bin/python

from Ontology import *
from LibSVMPredictor import *
from ArtificialPredictor import *
from PatternSpace import *
#from FeatureHandler import *

import os
import re
import sys
import glob
import string
import time
from multiprocessing import Pool, Lock

def main():

    #if len(sys.argv) < 5:
    #    print 'usage: ./prog -ip <test_path> -en <experiment_name>'
    #    print 'options: '
    #    print '-ni <value> - number of iterations for the simulated annealing process. (default: 3000)'
    #    print '-et <value> - experiment type. It can be "regular" or "synthetic". (default: synthetic)'
    #    print '-mp <value> - multiprocessing mode. <value> is the # of allowed simultaneous processes. (default: 2)'
    #    print '-di <value> - allow for dynamic inference. (default: 0) The -tb option is automatically 1 when -di is 1.'
    #    print '-tb <value> - allow temporal bonds. <values> can be 1 or 0 for True or False, respectively. (default: 0)'
    #else:
    #    for i in range(1,len(sys.argv)):
    #        if sys.argv[i] == ''

    if len(sys.argv) < 7:
        print './mp_real.py test_files_path experiment_name output_path synthetic|regular bond_weight_filename feature_thresh [OPTIONS]'
        print 'OPTIONS:'
        print '-topk <integer num> - number of top configuration to be considered'
        print '-tb  - with temporal bonds'
        print '-ntb - no temporal bonds'
        print '-di  - dynamic inference'
        print '-ndi - no dynamic inference'
        exit(1)

    # root path where the test files are
    test_files_path = sys.argv[1] # 'multiple_shot_test/4shots'
    experiment_name = sys.argv[2] #'youcook_4shots_temporalbonds'
    output_path = sys.argv[3]
    experiment_type = sys.argv[4]
    bond_weight_filename = sys.argv[5]
    feature_thresh = float(sys.argv[6])

#    experiment_type = 'regular'
    with_temporal_bonds = False
    dynamic_inference = False

    # number of top configurations to be considered
    top_k = 1

    for i in range(7,len(sys.argv)):
        if sys.argv[i] == '-tb':
            with_temporal_bonds = True
        elif sys.argv[i] == '-ntb':
            with_temporal_bonds = False
        elif sys.argv[i] == '-di':
            dynamic_inference = True
        elif sys.argv[i] == '-ndi':
            dynamic_inference = False
        elif sys.argv[i] == '-topk':
            if i+1 < len(sys.argv):
                try: 
                    top_k = int(sys.argv[i+1])
                except ValueError:
                    top_k = 1
                    print 'ERROR: top_k was set to 1 since no number was passed!'
                    print 'This might be an error in setting the input to the program. Please, revise it!'


    print 'top_k =',top_k

    # set the total number of parallel workers
    number_of_processes = 4

    # simulated annealing total number of iterations
    number_of_iterations = 3000

    # execute experiments
    run(output_path, experiment_name, test_files_path, bond_weight_filename, number_of_iterations, feature_thresh, dynamic_inference, with_temporal_bonds,
        experiment_type, number_of_processes, top_k, [[2, 2, 1], [70, 70, 10]])

def synthetic_experiment(args):
##### READ PARAMETERS
    # output path -- place where all data will be stored
    output_path = args[0]

    # feature test file
    infile = args[1]

    # parameters of experimental setting
    degradation_level = args[2]
    rank_level = args[3]
    ont_power = args[4]

    # Pattern Theory-based ontology
    ont = args[5]
    generator_space_filename = args[6]  #'youcook_multiple-shot_gspace_ptf.txt'
    bond_weights_filename = args[7]     #'youcook_bond_weights_ptf.txt'

    # experiment parameters
    number_of_trials = args[8]
    number_of_iterations = args[9]

    # setting paths
    groundtruth_config_path = args[10]
    scores_path = args[11]

    dynamic_inference = args[12]
    with_temporal_bonds = args[13]
    experiment_name = args[14]

    top_k = args[15]

    feature_support_thresh = args[16]

    strict_mode = True

#### SETTING OUTPUT PATHS

    videoname = infile.strip().split('/')[-1].split('.')[0]

    os.system("mkdir -p " + output_path)

    # create the directory
    full_scores_path = output_path + '/' + experiment_name + '_' + scores_path+'_'+repr(degradation_level)+'dl_' + repr(ont_power) + 'op_' + repr(rank_level) + 'rnk'
    if os.path.isdir(full_scores_path) == False:
        os.system('mkdir ' + full_scores_path)

    video_results_path = output_path + '/' + experiment_name + '_' + 'results_'+repr(degradation_level)+'dl_' + repr(ont_power) + 'op_' + repr(rank_level) + 'rnk'
    if os.path.isdir(video_results_path) == False:
        os.system('mkdir ' + video_results_path)
    if os.path.isdir(video_results_path+'/'+videoname) == False:
        os.system('mkdir '+video_results_path+'/'+videoname)

######## EXPERIMENT
    #dynamic_inference = True
    trials_performance_records = []
    for i in range(number_of_trials):
        # set up synthetic predictor (which is specific for each test file; because of label score pre-computation)
        pred = ArtificialPredictor(generator_space_filename, infile, 'degradation', 0.01 * degradation_level, rank_level, os.getpid())

        # create pattern inference environment
        ps = PatternSpace(ont, pred, infile, groundtruth_config_path + '/' + videoname + '_gt.ptg', bond_weights_filename, strict_mode)

        # create global jump configuration
        global_jump_config = ps.create_global_jump_configuration()

        # get baseline configuration -- label each feature based on the best score prediction
        baseline_config = ps.get_baseline_configuration(global_jump_config)

        # start the Pattern Theory-based inference process
        if dynamic_inference:
            with_temporal_bonds = True

#            print 'read first set of features...'

            initial_configuration = Configuration()
            new_features_available, dynamic_global_jump_config = ps.add_next_features(initial_configuration)

#            print 'First configuration: '
#            initial_configuration.print_info()
#            os.system('read -p "pause"')

            initial_configuration = ps.global_proposal.propose(dynamic_global_jump_config, with_temporal_bonds)

            #initial_configuration = ps.local_proposal.time_based_propose(initial_configuration,
            #                                                              initial_configuration.get_current_time())
            # optimize the initial configuration using 'regular' inference
#            print 'Optimize initial configuration using regular global and local proposals: '
#            os.system('read -p "pause"')
            #print 'BEFORE...' + video_results_path+'/'+videoname
            (bests_configs,bests_energies,bests_accuracies,sorted_top_k_configs) = \
                    ps.mcmc_simulated_annealing_inference(videoname, number_of_iterations, dynamic_global_jump_config,
                                                          video_results_path+'/'+videoname, False, with_temporal_bonds,
                                                          top_k, initial_configuration)
            initial_configuration = sorted_top_k_configs[0][0]
            #print 'Initial Config: '
            #initial_configuration.print_info()

#            print 'Optimized initial configuration: '
#            initial_configuration.print_info()
#            os.system('read -p "pause"')

            new_features_available, dynamic_global_jump_config = ps.add_next_features(initial_configuration,
                                                                                      dynamic_global_jump_config)
            while new_features_available:
                #print 'read next set of features...'

                # delete reference for the configuration in the sorted list
                del sorted_top_k_configs[0]
                for k in range(len(sorted_top_k_configs)):
                    ps.dispose_configuration(sorted_top_k_configs[k][0])
                del sorted_top_k_configs[:]

                # find the optimal configuration for the current set of features
                (bests_configs,bests_energies,bests_accuracies,sorted_top_k_configs) = \
                    ps.mcmc_simulated_annealing_inference(videoname, number_of_iterations, dynamic_global_jump_config,
                                                          video_results_path+'/'+videoname, dynamic_inference, with_temporal_bonds,
                                                          top_k, initial_configuration)
                # update initial configuration
                initial_configuration = sorted_top_k_configs[0][0]
                #print 'Updated Config: '
                #initial_configuration.print_info()

                # read new incoming features
                new_features_available, dynamic_global_jump_config = ps.add_next_features(initial_configuration,
                                                                                          dynamic_global_jump_config)
        else:
            (bests_configs,bests_energies,bests_accuracies,sorted_top_k_configs) = \
                    ps.mcmc_simulated_annealing_inference(videoname, number_of_iterations, global_jump_config,
                                                          video_results_path+'/'+videoname, feature_support_thresh, dynamic_inference, with_temporal_bonds, top_k)

        # (global_tp,global_fp,global_bond_score,global_bond_misses) = ps.compute_performance_rate(bests_configs)

######## PERFORMANCE MEASUREMENTS

        # compute the baseline's performance counting the percentage of correct support bonds (specific feature labeling)
        baseline_accuracy = ps.get_accuracy_score(baseline_config)

        # compute the baseline' performance counting the percentage of generators in the generator set that agrees with
        # ground-truth configuration's generator set
        baseline_concept_score = ps.concepts_score_hits(baseline_config)

        best_config_accuracy = []
        best_concept_score = []
        for j in range(len(sorted_top_k_configs)):
            best_config_accuracy.append(ps.get_accuracy_score(sorted_top_k_configs[j][0]))
            best_concept_score.append(ps.concepts_score_hits(sorted_top_k_configs[j][0]))

        # prepare record
        trial_performance = []
        performance_records = videoname + ',' + repr(baseline_accuracy) + ',' + repr(baseline_concept_score)
        trial_performance.append(baseline_accuracy)
        trial_performance.append(baseline_concept_score)
        for j in range(len(best_config_accuracy)):
            performance_records += ',' + repr(best_config_accuracy[j]) + ',' + repr(best_concept_score[j])
            trial_performance.append(best_config_accuracy[j])
            trial_performance.append(best_concept_score[j])

        # record performance rates on file
        #accuracy_file.write(performance_records + '\n')
        trials_performance_records.append(trial_performance)

        # display on screen the record performance rates on screen
        #print 'Performance Rates'
        #print '<video name> <support bond rate> <generator set rate> ...'
        print performance_records

        #os.system("read -p 'pause'")

        del best_config_accuracy
        del best_concept_score

######## RECORD THE COMPUTED CONFIGURATIONS ON FILES

#        print 'saving computed configurations...'
        # save the baseline configuration on a file
        baseline_config_filename = video_results_path + '/baseline_' + videoname + '.txt'
        ps.save_configuration(baseline_config_filename, baseline_config)

        # save each output configuration from the lowest energy to the highest
        for j in range(len(sorted_top_k_configs)):
            best_config_save_filename = video_results_path + '/' + videoname + '/' + videoname + '_best_config_rank' + repr(j+1) + '.txt'
            ps.save_configuration(best_config_save_filename,sorted_top_k_configs[j][0])

        # save
#        print 'deleting score files...'

        #os.system('cp ' + str(os.getpid()) + '_*.scores ' + full_scores_path + '/')
        #os.system('cp ' + '*.scores ' + full_scores_path + '/')
        #os.system('rm *.scores')
        #os.system('rm ' + str(os.getpid()) + '_*.scores')
        #os.system('rm *.sls')

        # free memory
        del ps

##### RECORD THE COMPUTED PERFORMANCE ON FILE

    rate_sums = [0.0] * len(trials_performance_records[0])
#    print 'rate_sums: ' + repr(rate_sums)
    for i in range(len(trials_performance_records)):
        for j in range(len(trials_performance_records[i])):
            rate_sums[j] += trials_performance_records[i][j]

#    print 'prepare printable performance records...'
    performance_records = videoname
    for i in range(len(rate_sums)):
        performance_records += ',' + repr(rate_sums[i] / number_of_trials)

    # open file on write mode to record performance rates on a global performance rate file
    #lock.acquire()
#    performance_record_filename = 'performance_'+repr(os.getpid())+'_'+repr(degradation_level)+'dl_' + repr(ont_power) + 'op_' + repr(rank_level) + 'rnk.txt'
    performance_record_filename = output_path + '/' + experiment_name + '_performance_'+repr(degradation_level)+\
                                  'dl_' + repr(ont_power) + 'op_' + repr(rank_level) + 'rnk.txt'
    performance_record_file = open(performance_record_filename,'a')
    performance_record_file.write(performance_records + '\n')
    performance_record_file.close()
    #lock.release()

#    print 'returning...'
    return performance_record_filename

def real_data_experiment(args):
    ##### READ PARAMETERS
    output_path = args[0]

    # feature test file
    infile = args[1]

    # Pattern Theory-based ontology
    ont = args[2]
    pred = args[3]
    bond_weights_filename = args[4]     #'youcook_bond_weights_ptf.txt'

    # experiment parameters
    number_of_trials = args[5]
    number_of_iterations = args[6]

    # new params -- 2015
    feature_support_thresh = args[7]

    # setting paths
    groundtruth_config_path = args[8]
    scores_path = args[9]

    dynamic_inference = args[10]
    with_temporal_bonds = args[11]
    experiment_name = args[12]

    top_k = args[13]
    print 'real data experiments top_k:',top_k

    strict_mode = True

    videoname = infile.strip().split('/')[-1].split('.')[0]

    os.system('mkdir -p ' + output_path)

    full_scores_path = output_path + '/' + experiment_name + '_' + scores_path
    if os.path.isdir(full_scores_path) == False:
        os.system('mkdir -p ' + full_scores_path)

    full_results_path = output_path + '/' + experiment_name + '_' +'results'
    if os.path.isdir(full_results_path) == False:
        os.system('mkdir -p '+ full_results_path)

    video_results_path = full_results_path + '/' + videoname
    if os.path.isdir(video_results_path) == False:
        os.system('mkdir -p ' + video_results_path)

    trials_performance_records = []
    for i in range(number_of_trials):
        # set the pattern theory environment (the generator space)
        ps = PatternSpace(ont, pred, infile, groundtruth_config_path+'/'+videoname+'_gt.ptg', bond_weights_filename, strict_mode)

        # create global jump configuration
        global_jump_config = ps.create_global_jump_configuration()
        if len(global_jump_config.get_feature_generators()) < 1: return None # performance file created

        # get baseline configuration -- label each feature based on the best score prediction
        baseline_config = ps.get_baseline_configuration(global_jump_config)

        # do the inference
        (bests_configs,bests_energies,bests_accuracies,sorted_top_k_configs) = \
            ps.mcmc_simulated_annealing_inference(videoname, number_of_iterations, global_jump_config,
                                                  video_results_path, feature_support_thresh, dynamic_inference,
                                                  with_temporal_bonds, top_k)

######## PERFORMANCE MEASUREMENTS

        # compute the baseline's performance counting the percentage of correct support bonds (specific feature labeling)
        baseline_accuracy = ps.get_accuracy_score(baseline_config)

        # compute the baseline' performance counting the percentage of generators in the generator set that agrees with
        # ground-truth configuration's generator set
        baseline_concept_score = ps.concepts_score_hits(baseline_config)

        best_config_accuracy = []
        best_concept_score = []
        for j in range(len(sorted_top_k_configs)):
            best_config_accuracy.append(ps.get_accuracy_score(sorted_top_k_configs[j][0]))
            best_concept_score.append(ps.concepts_score_hits(sorted_top_k_configs[j][0]))

        # prepare record
        trial_performance = []
        performance_records = videoname + ',' + repr(baseline_accuracy) + ',' + repr(baseline_concept_score)
        trial_performance.append(baseline_accuracy)
        trial_performance.append(baseline_concept_score)
        for j in range(len(best_config_accuracy)):
            performance_records += ',' + repr(best_config_accuracy[j]) + ',' + repr(best_concept_score[j])
            trial_performance.append(best_config_accuracy[j])
            trial_performance.append(best_concept_score[j])

        # record performance rates on file
        #accuracy_file.write(performance_records + '\n')
        trials_performance_records.append(trial_performance)

        # display on screen the record performance rates on screen: print '<video name> <support bond rate> <generator set rate> ...'
        print performance_records

        #os.system("read -p 'pause'")

        del best_config_accuracy
        del best_concept_score

        baseline_config_filename = video_results_path + '/baseline_' + videoname + '.txt'
        ps.save_configuration(baseline_config_filename, baseline_config)

        print 'NUMBER OF BEST CONFIGURATIONS FOUND:',repr(len(sorted_top_k_configs))
        for j in range(len(sorted_top_k_configs)):
            best_config_save_filename = video_results_path + '/' + videoname + '_best_config_rank' + repr(j+1) + '.txt'
            print best_config_save_filename
            ps.save_configuration(best_config_save_filename,sorted_top_k_configs[j][0])

        del ps

##### CLEANING
    feature_generators = baseline_config.get_feature_generators()
    for generator in feature_generators:
        feature_filename = generator.get_features().split('/')[-1]
        feature_scores_filename = str(os.getpid()) + '*' + feature_filename + '.scores'
        os.system('cp ' + feature_scores_filename + ' ' + full_scores_path + '/')
        os.system('rm ' + feature_scores_filename)
        #os.system('rm ' + feature_scores_filename)
    #os.system('rm *.sls') #spatial constraint

##### RECORD THE COMPUTED PERFORMANCE ON FILE

    rate_sums = [0.0] * len(trials_performance_records[0])
#    print 'rate_sums: ' + repr(rate_sums)
    for i in range(len(trials_performance_records)):
        for j in range(len(trials_performance_records[i])):
            rate_sums[j] += trials_performance_records[i][j]

#    print 'prepare printable performance records...'
    performance_records = videoname
    for i in range(len(rate_sums)):
        performance_records += ',' + repr(rate_sums[i] / number_of_trials)

    # open file on write mode to record performance rates on a global performance rate file
    performance_record_filename = output_path + '/' + experiment_name + '_performance.txt'
    performance_record_file = open(performance_record_filename,'a')
    performance_record_file.write(performance_records + '\n')
    performance_record_file.close()

#    print 'returning...'
    return performance_record_filename

def read_synthetic_experiment_params(synthetic_experiment_params):
    rank_params_index = 0
    degradation_params_index = 1

    rank_start = -1
    rank_end = 0
    rank_step = 1
    if synthetic_experiment_params[rank_params_index]:
        rank_start = synthetic_experiment_params[rank_params_index][0]
        rank_end = synthetic_experiment_params[rank_params_index][1]+1
        if len(synthetic_experiment_params[rank_params_index]) > 2:
            rank_step = synthetic_experiment_params[rank_params_index][2]

    degrad_start = 10
    degrad_end = 101
    degrad_step = 10
    if synthetic_experiment_params[degradation_params_index]:
        degrad_start = synthetic_experiment_params[degradation_params_index][0]
        degrad_end = synthetic_experiment_params[degradation_params_index][1]+1
        if len(synthetic_experiment_params[degradation_params_index]) > 2:
            degrad_step = synthetic_experiment_params[degradation_params_index][2]

    return rank_start,rank_end,rank_step,degrad_start,degrad_end,degrad_step

def run(output_path, experiment_name, test_files_path, bond_weights_filename, number_of_iterations, feature_thresh,
        dynamic_inference=False, with_temporal_bonds=False, experiment_type='regular', number_of_processes='4',
        top_k=3, synthetic_experiment_params=[[],[]]):
    random.seed(12345)

    print 'run top_k',top_k

    # create pool of workers
    pool = None
    if number_of_processes > 1:
        pool = Pool(number_of_processes)
    #lock = Lock()

    # create output path if does not exist yet
    if os.path.isdir(output_path) == False: os.system('mkdir -p ' + output_path)

    # setting input file paths
    generator_space_filename = 'breakfast_generator_space_no_tmp_obj.txt'

    #bond_weights_filename = 'youcook_bond_weights_ptf.txt'

    # prepare support vector machine based predictor
    pred = LibSVMPredictor('SVM', 'hof', 'breakfast_models_s1.txt', 'breakfast_labels.txt', './libsvm-3.17')

    # set up ontology information
    ont = Ontology(generator_space_filename, 'breakfast_modalities.txt', 'breakfast_priors.txt')

    # number of times that the algorithm is applied to each test file
    number_of_trials = 1

    groundtruth_config_path = ''
    scores_path = 'scores'

    count = 0.0
    ont_power = -1
    is_synthetic_experiment = False
    if experiment_type == 'synthetic':
        is_synthetic_experiment = True

    # collect the list of test files to be processed
    input_test_files = glob.glob( os.path.join(test_files_path, '*.txt') )

    ##### SYNTHETIC EXPERIMENT #####
    if is_synthetic_experiment == True:
        # unwrapping synthetic params
        rank_start, rank_end, rank_step, degrad_start, degrad_end, degrad_step = \
            read_synthetic_experiment_params(synthetic_experiment_params)

        for rank_level in range(rank_start, rank_end, rank_step):
            for degradation_level in range(degrad_start, degrad_end, degrad_step):
                # assemble tasks
                tasks = []
                for infile in input_test_files:
                    tasks.append((output_path, infile, degradation_level, rank_level, ont_power, ont, generator_space_filename,
                                  bond_weights_filename, number_of_trials, number_of_iterations, groundtruth_config_path,
                                  scores_path, dynamic_inference, with_temporal_bonds, experiment_name, top_k))
                # multiprocess tasks
                # sequential...
                #for i in range(len(tasks)):
                #    synthetic_experiment(tasks[i])
                # multiprocessing...
                pool.map(synthetic_experiment, tasks)

    else:
        # assemble tasks
        tasks = []
        for infile in input_test_files:
            #print 'filename:',infile
            tasks.append((output_path, infile, ont, pred, bond_weights_filename, number_of_trials, number_of_iterations,
                          feature_thresh, groundtruth_config_path, scores_path, dynamic_inference, with_temporal_bonds,
                          experiment_name, top_k))

        # multiprocessing with threads
        if number_of_processes > 1:
            pool.map(real_data_experiment, tasks)
        # processing with a single thread
        else:
            #time_file = open('time_measurements.txt','w')
            for i in range(len(tasks)):
                time_file = open(experiment_name + 'time_measurements.csv','a')
                start_time = time.clock()
                #print 'start time:',start_time
                real_data_experiment(tasks[i])
                elapsed_time = time.clock() - start_time
                #print 'elapsed time: ',repr(elapsed_time)
                #print repr(tasks[i][1]) + ',' + repr(elapsed_time) + '\n'
                time_file.write(tasks[i][1] + ',' + repr(elapsed_time) + '\n')
                time_file.close()
            #time_file.close()
        #pool.map(real_data_experiment, tasks)

if __name__ == "__main__":
    main()
    #           accuracy_average = trials_accuracy_sum/number_of_trials
    #
