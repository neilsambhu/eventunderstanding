#!/usr/bin/python

from Ontology import *
from LibSVMPredictor import *
from ArtificialPredictor import *
from PatternSpace import *
#from FeatureHandler import *

import os
import re
import glob
import string
import time
from multiprocessing import Pool, Lock


def main():

    # root path where the test files are
    test_files_path = 'multiple_shot_test/3shots' #'test/3shots'
    experiment_name = '3shots_notemporalbonds'
    with_temporal_bonds = True

    # set the type of experiment
    experiment_type = 'synthetic' # could be 'regular'

    # set the total number of parallel workers
    number_of_processes = 2

    # simulated annealing total number of iterations
    number_of_iterations = 3000

    # execute experiments
    run(experiment_name, test_files_path, number_of_iterations, with_temporal_bonds,
        number_of_processes, experiment_type, [[2,3,1],[10,30,10]])

def synthetic_experiment(args):
##### READ PARAMETERS

    # feature test file
    infile = args[0]

    # parameters of experimental setting
    degradation_level = args[1]
    rank_level = args[2]
    ont_power = args[3]

    # Pattern Theory-based ontology
    ont = args[4]
    generator_space_filename = args[5]  #'youcook_multiple-shot_gspace_ptf.txt'
    bond_weights_filename = args[6]     #'youcook_bond_weights_ptf.txt'

    # experiment parameters
    number_of_trials = args[7]
    number_of_iterations = args[8]

    # setting paths
    groundtruth_config_path = args[9]
    scores_path = args[10]

    with_temporal_bonds = args[11]
    experiment_name = args[12]

    strict_mode = True

    videoname = infile.strip().split('/')[-1].split('.')[0]

    # create the directory
    full_scores_path = experiment_name + '_' + scores_path+'_'+repr(degradation_level)+'dl_' + repr(ont_power) + 'op_' + repr(rank_level) + 'rnk'
    if os.path.isdir(full_scores_path) == False:
        os.system('mkdir ' + full_scores_path)

    video_results_path = experiment_name + '_' + 'results_'+repr(degradation_level)+'dl_' + repr(ont_power) + 'op_' + repr(rank_level) + 'rnk'
    if os.path.isdir(video_results_path) == False:
        os.system('mkdir ' + video_results_path)
    if os.path.isdir(video_results_path+'/'+videoname) == False:
        os.system('mkdir '+video_results_path+'/'+videoname)

    trials_performance_records = []
    for i in range(number_of_trials):
        # set up synthetic predictor (which is specific for each test file; because of label score pre-computation)
        pred = ArtificialPredictor(generator_space_filename, infile, 'degradation', 0.01*degradation_level, rank_level, os.getpid())

        # create pattern inference environment
        ps = PatternSpace(ont, pred, infile, groundtruth_config_path + '/' + videoname + '_gt.ptg', bond_weights_filename, strict_mode)

        # create global jump configuration
        global_jump_config = ps.create_global_jump_configuration()

        # get baseline configuration -- label each feature based on the best score prediction
        baseline_config = ps.get_baseline_configuration(global_jump_config)

        # start the Pattern Theory-based inference process
        (bests_configs,bests_energies,bests_accuracies,sorted_top_k_configs) = \
            ps.mcmc_simulated_annealing_inference(videoname, number_of_iterations, global_jump_config, video_results_path, with_temporal_bonds)
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
        print 'Performance Rates'
        print '<video name> <support bond rate> <generator set rate> ...'
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
        os.system('cp ' + str(os.getpid()) + '_*.scores ' + full_scores_path + '/')
        os.system('rm ' + str(os.getpid()) + '_*.scores')
        #os.system('rm *.sls')

        # free memory
        del ps

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
    performance_record_filename = experiment_name + '_performance_'+repr(degradation_level)+'dl_' + repr(ont_power) + 'op_' + repr(rank_level) + 'rnk.txt'
    performance_record_file = open(performance_record_filename,'a')
    performance_record_file.write(performance_records + '\n')
    performance_record_file.close()
    #lock.release()

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

def run(experiment_name, test_files_path, number_of_iterations, with_temporal_bonds=False, number_of_processes='4',
        experiment_type='regular', synthetic_experiment_params=[[],[]]):
    random.seed(12345)

    # create pool of workers
    pool = Pool(number_of_processes)
    #lock = Lock()

    # setting input file paths
    generator_space_filename = 'youcook_multiple-shot_gspace_ptf.txt'
    bond_weights_filename = 'youcook_bond_weights_ptf.txt'

    # prepare support vector machine based predictor
    pred = LibSVMPredictor('SVM','hof','youcook_models_ptf.txt','youcook_label_ids_ptf.txt','./libsvm-3.17')

    # set up ontology information
    ont = Ontology(generator_space_filename,'youcook_modalities.txt','youcook_priors.txt')

    # number of times that the algorithm is applied to each test file
    number_of_trials = 1

    groundtruth_config_path = 'video_shot_gtgraphs'
    scores_path = 'scores_'

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
            for degradation_level in range(degrad_start,degrad_end,degrad_step):
                # assemble tasks
                tasks = []
                for infile in input_test_files:
                    tasks.append((infile, degradation_level, rank_level, ont_power, ont, generator_space_filename,
                                  bond_weights_filename, number_of_trials, number_of_iterations, groundtruth_config_path,
                                  scores_path, with_temporal_bonds, experiment_name))
                # multiprocess tasks
                pool.map(synthetic_experiment, tasks)

    else:
        experiment_id = number_of_iterations
        global_acc = 0.0
        global_tp = 0.0
        global_fp = 0.0
        bests_configs = None
        bests_energies = None
        bests_accuracies = None
        strict_mode = True
        total_accuracy = 0.0

        for infile in glob.glob( os.path.join(test_files_path, '*.txt') ):
            print 'processing ' + infile
            accuracy_file = open('accuracy_exp'+repr(experiment_id)+'.txt','a')
            names = string.split(infile,'/')
            videoname = string.split(names[len(names)-1],".")[0]

            full_scores_path = scores_path + '_exp'+ repr(experiment_id)
            if os.path.isdir(full_scores_path) == False:
                os.system('mkdir ' + full_scores_path)

            full_results_path = 'results_config_exp'+ repr(experiment_id)
            if os.path.isdir(full_results_path) == False:
                os.system('mkdir '+ full_results_path)

            video_results_path = full_results_path + '/' + videoname
            if os.path.isdir(video_results_path) == False:
                os.system('mkdir '+video_results_path)

            trials_accuracy_sum = 0.0
            for i in range(number_of_trials):
                # set the pattern theory environment (the generator space)
                ps = PatternSpace(ont, pred, infile, groundtruth_config_path+'/'+videoname+'_gt.ptg', 'youcook_bond_weights_ptf.txt', strict_mode)
                # get a configuration containing only feature generators
                global_jump_config = ps.create_global_jump_configuration()

                baseline_config = ps.get_baseline_configuration(global_jump_config)
                print 'BASELINE ACCURACY'
                baseline_accuracy = ps.get_accuracy_score(baseline_config)
                baseline_concept_score = ps.concepts_score_hits(baseline_config)
                ps.save_configuration(video_results_path + '/baseline_' + videoname + '.txt',baseline_config)

                (bests_configs,bests_energies,bests_accuracies,sorted_top_k_configs) = ps.mcmc_simulated_annealing_inference(videoname, number_of_iterations, global_jump_config, video_results_path)
                ##(global_acc,global_tp,global_fp,global_bond_score,global_bond_misses) = ps.get_top_k_accuracy_score(bests_configs)

                # last one used:
                #(global_tp,global_fp,global_bond_score,global_bond_misses) = ps.compute_performance_rate(bests_configs)
                #accuracy_file.write(videoname + ' ' + repr(baseline_accuracy) + ' ' + repr(0.0) + ' ' + repr(global_tp) + ' ' + repr(global_fp) + ' ' + repr(global_bond_score) + ' ' + repr(global_bond_misses) + '\n')
                #print videoname + ' ' + repr(baseline_accuracy) + ' ' + repr(0.0) + ' ' + repr(global_tp) + ' ' + repr(global_fp) + ' ' + repr(global_bond_score) + ' ' + repr(global_bond_misses)

                print 'BEST CONFIG ACCURACY'
                best_config_accuracy = []
                best_concept_score = []
                for j in range(len(sorted_top_k_configs)):
                    best_config_accuracy.append(ps.get_accuracy_score(sorted_top_k_configs[j][0]))
                    best_concept_score.append(ps.concepts_score_hits(sorted_top_k_configs[j][0]))

                accuracy_file.write(videoname + ',' + repr(baseline_accuracy) + ',' + repr(baseline_concept_score))
                for j in range(len(best_config_accuracy)):
                    accuracy_file.write(',' + repr(best_config_accuracy[j]) + ',' + repr(best_concept_score[j]))
                accuracy_file.write('\n')
                print videoname + ',' + repr(baseline_accuracy) + ',' + repr(best_config_accuracy[0]) + ',' + repr(baseline_concept_score) + ',' + repr(best_concept_score[0])

                del best_config_accuracy
                del best_concept_score

                for j in range(len(sorted_top_k_configs)):
                    best_config_save_filename = video_results_path + '/' + videoname + '_best_config_rank' + repr(j+1) + '.txt'
                    ps.save_configuration(best_config_save_filename,sorted_top_k_configs[j][0])

                trials_accuracy_sum += global_acc
            del ps

            accuracy_average = trials_accuracy_sum / number_of_trials
            total_accuracy += accuracy_average
            count += 1.

            os.system('cp *.scores ' + full_scores_path + '/')
            os.system('rm *.scores')
            os.system('rm *.sls')
            accuracy_file.close()

if __name__ == "__main__":
    main()
    #           accuracy_average = trials_accuracy_sum/number_of_trials
    #