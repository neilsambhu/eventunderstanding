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

def artificial_run():
    pass

def real_data_run():
    pass

def main():
    number_of_iterations = 3002
    while number_of_iterations < 3003:
        run(number_of_iterations)
        number_of_iterations += 500

def run(number_of_iterations):
    # prepare support vector machine based predictor
    #pred = LibSVMPredictor('SVM','hof','youcook_models_ptf.txt','youcook_label_ids_ptf.txt','./libsvm-3.17')
    pred = LibSVMPredictor('SVM','hof','youcook_models_ptf.txt','youcook_label_ids_ptf.txt','./libsvm-3.17')

    # set up ontology information
    ont = Ontology('youcook_multiple-shot_gspace_ptf.txt','youcook_modalities.txt','youcook_priors.txt')

    random.seed(12345)

    # number of times that the algorithm is applied to each test file
    number_of_trials = 1
    
    # simulated annealing total number of iterations
    #number_of_iterations = 2500
    
    # root path where the test files are
    test_files_root_path = 'test/3shots'
    groundtruth_config_path = 'video_shot_gtgraphs'

    count = 0.0
    trials_average = 0.0
    total_accuracy = 0.0
    accuracy_average = 0.0

    scores_path = 'scores_'
    degradation_level = 1
    ont_power = -1
    is_artificial_experiment = True

    ##### ARTIFICIAL EXPERIMENT #####
    if is_artificial_experiment == True:
        for rank_level in range(1,6,6):
            #rank_level = -1
            for degradation_level in range(10,100,101):
                global_acc = 0.0
                global_tp = 0.0
                global_fp = 0.0

                bests_configs = None
                bests_energies = None
                bests_accuracies = None

                strict_mode = True
                total_accuracy = 0.0

                for infile in glob.glob( os.path.join(test_files_root_path, '*.txt') ):

                    accuracy_file = open('accuracy_strict_'+repr(degradation_level)+'dl_' + repr(ont_power) + 'op_' + repr(rank_level) + 'rnk.txt','a')
                    names = string.split(infile,'/')
                    videoname = string.split(names[len(names)-1],".")[0]

                    if os.path.isdir(scores_path+'_'+repr(degradation_level)+'dl_' + repr(ont_power) + 'op_' + repr(rank_level) + 'rnk') == False:
                        os.system('mkdir ' + scores_path + '_'+repr(degradation_level)+'dl_' + repr(ont_power) + 'op_' + repr(rank_level) + 'rnk')

                    if os.path.isdir('results_'+repr(degradation_level)+'dl_' + repr(ont_power) + 'op_' + repr(rank_level) + 'rnk') == False:
                        os.system('mkdir results_'+repr(degradation_level)+'dl_' + repr(ont_power) + 'op_' + repr(rank_level) + 'rnk')

                    video_results_path = 'results_'+repr(degradation_level)+'dl_' + repr(ont_power) + 'op_' + repr(rank_level) + 'rnk'

                    if os.path.isdir(video_results_path+'/'+videoname) == False:
                        os.system('mkdir '+video_results_path+'/'+videoname)

                    trials_accuracy_sum = 0.0
                    for i in range(number_of_trials):
                        pred = ArtificialPredictor('youcook_multiple-shot_gspace_ptf.txt',infile,'degradation',0.01*degradation_level,rank_level)
                        ps = PatternSpace(ont, pred, infile, groundtruth_config_path + '/' + videoname + '_gt.ptg', 'youcook_bond_weights_ptf.txt', strict_mode)
                        global_jump_config = ps.create_global_jump_configuration()

                        baseline_config = ps.get_baseline_configuration(global_jump_config)
                        baseline_accuracy = ps.get_accuracy_score(baseline_config)
                        baseline_concept_score = ps.concepts_score_hits(baseline_config)
                        ps.save_configuration(video_results_path + '/baseline_' + videoname + '.txt',baseline_config)

                        (bests_configs,bests_energies,bests_accuracies,sorted_top_k_configs) = ps.mcmc_simulated_annealing_inference(videoname, number_of_iterations, global_jump_config, video_results_path)
                        #			            (global_tp,global_fp,global_bond_score,global_bond_misses) = ps.compute_performance_rate(bests_configs)

                        #			            accuracy_file.write(videoname + ' ' + repr(baseline_accuracy) + ' ' + repr(0.0) + ' ' + repr(global_tp) + ' ' + repr(global_fp) + ' ' + repr(global_bond_score) + ' ' + repr(global_bond_misses) + '\n')
                        #			            print videoname + ' ' + repr(baseline_accuracy) + ' ' + repr(0.0) + ' ' + repr(global_tp) + ' ' + repr(global_fp) + ' ' + repr(global_bond_score) + ' ' + repr(global_bond_misses)

                        print 'BEST CONFIG ACCURACY'
                        best_config_accuracy = []
                        best_concept_score = []
                        for j in range(len(sorted_top_k_configs)):
                            best_config_accuracy.append(ps.get_accuracy_score(sorted_top_k_configs[j][0]))
                            best_concept_score.append(ps.concepts_score_hits(sorted_top_k_configs[j][0]))

                        accuracy_file.write(videoname + ',' + repr(baseline_accuracy) + ',' + repr(baseline_accuracy))
                        for j in range(len(best_config_accuracy)):
                            accuracy_file.write(',' + repr(best_config_accuracy[j]) + ',' + repr(best_concept_score[j]))
                        accuracy_file.write('\n')
                        print videoname + ',' + repr(baseline_accuracy) + ',' + repr(best_config_accuracy[0]) + ',' + repr(baseline_concept_score) + ',' + repr(best_concept_score[0])

                        os.system("read -p 'pause'")

                        del best_config_accuracy
                        del best_concept_score

                        for j in range(len(sorted_top_k_configs)):
                            best_config_save_filename = video_results_path + '/' + videoname + '/' + videoname + '_best_config_rank' + repr(j+1) + '.txt'
                            ps.save_configuration(best_config_save_filename,sorted_top_k_configs[j][0])

                        trials_accuracy_sum += global_acc
                        del ps

                    accuracy_average = trials_accuracy_sum / number_of_trials
                    total_accuracy += accuracy_average
                    count += 1.

                    os.system('cp *.scores ' + scores_path+'_'+repr(degradation_level)+'dl_' + repr(ont_power) + 'op_' + repr(rank_level) + 'rnk/')
                    os.system('rm *.scores')
                    #os.system('rm *.sls')

                    accuracy_file.close()

            print 'AVERAGE ACCURACY: ' + repr(total_accuracy/count)


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

        for infile in glob.glob( os.path.join(test_files_root_path, '*.txt') ):
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
