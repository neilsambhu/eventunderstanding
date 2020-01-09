#!/usr/bin/python

from Label import *
from Feature import *
from GlobalProposal import *
from LocalProposal import *

import os
import math
import string


class PatternSpace:

    def __init__(self, ont, pred, features_filename, gt_filename, bond_weights_filename=None, strict_mode=True):
        self.__ontology = ont
        self.__predictor = pred # A dictionary of pointers to predictors (visual detectors)
        self.__features = []
        self.__strict_mode = strict_mode
        self.__gt_filename = gt_filename

        self.__bond_weights = None
        self.__read_bond_weights_file(bond_weights_filename)

        self.__global_proposal_chance = 1.; #0.45
        self.__local_proposal_chance = 1. - self.__global_proposal_chance
        self.global_proposal = GlobalProposal(ont, pred, strict_mode)
        self.local_proposal = LocalProposal(ont, pred, self.__bond_weights, strict_mode)

        # this will be postponed for later so that we can work with an expanding window
        self.__read_feature_file(features_filename)

    #random.seed(12345)

    def __read_bond_weights_file(self,filename):
        if filename != None:
            self.__bond_weights = {}
            file = open(filename)
            for line in file:
                data = line.strip().split()
                if len(data) > 1:
                    self.__bond_weights[data[0]] = float(data[1])
            file.close()

    def __read_feature_file(self,filename):
        cost = 20
        x_min, x_max, y_min, y_max, t_min, t_max = 0, 0, 0, 0, 0, 0; #-1, -1, -1, -1, -1, -1;
        labels = [];
        feature_location = '';

        file = open(filename)
        for line in file:
            data = string.split(line.replace('\n',''))
            for i in range(3,len(data)):
                content = data[i].split(':');
                if content[0] == 'labels':
                    labels = content[1].split(',');
                elif content[0] == 'xmin':
                    x_min = int(content[1]);
                elif content[0] == 'xmax':
                    x_max = int(content[1]);
                elif content[0] == 'ymin':
                    y_min = int(content[1]);
                elif content[0] == 'ymax':
                    y_max = int(content[1]);
                elif content[0] == 'tmin':
                    t_min = int(content[1]);
                elif content[0] == 'tmax':
                    t_max = int(content[1]);
                elif content[0] == 'location':
                    feature_location = content[1];

            # labels = string.split(data[3],',') if len(data) > 3 else []
            # #name,path,time,cost,label,location
            # feature_location = data[4] if len(data) > 4 else ''
            # x_min = int(data[5]) if len(data) > 5 else -1
            # x_max = int(data[6]) if len(data) > 6 else -1
            # y_min = int(data[7]) if len(data) > 7 else -1
            # y_max = int(data[8]) if len(data) > 8 else -1
            # t_min = int(data[9]) if len(data) > 9 else -1
            # t_max = int(data[10]) if len(data) > 10 else -1

            self.__features.append(Feature(data[0], data[2], int(data[1]), cost, labels, feature_location,
                                           [x_min, x_max, y_min, y_max, t_min, t_max]))
        file.close()
    #print 'features: ' + repr(self.__features)

    ## for example, two configuration might come from different times, so that the connections
    ## could be possible through temporal bonds
    def bond_configurations(self,c_i,c_j):  ## futuristic method!!
        pass

    def save_configuration(self, filename, config):
        generators = config.get_generators()
        number_of_generators = len(generators)
        number_of_bonds = 0
        last_index = -1

        generators_types = {}
        generators_info = []
        bonds_info = []

        for g in generators:
            g.get_time().sort()
            generators_info.append( ( g.get_id(), g.get_name(), g.get_match_state(), 'level'+repr(g.get_level()),
                                      g.get_time()[last_index], g.get_type(), g.get_features() ) )
            generators_types[g.get_id()] = g.get_type()

            outbonds = g.get_outbonds()
            for b in outbonds:
                if b.get_connector() != None:
                    bonds_info.append( ( g.get_id(), b.get_connector(), b.get_match_state(), b.get_energy() ) )
                    number_of_bonds += 1

        file = open(filename,'w')
        file.write(repr(number_of_generators)+','+repr(number_of_bonds)+'\n')

        for g in generators_info:
            file.write(repr(g[0])+','+g[1]+','+repr(g[2])+','+g[3]+','+repr(g[4])+','+g[5]+','+str(g[6])+'\n')

        for b in bonds_info:
            file.write(repr(b[0])+','+repr(b[1])+','+repr(b[2])+','+repr(b[3])+',1\n')

        file.close()

    def __not_in_the_list(self, config, best_config_list):
        for j in range(len(best_config_list)):
            if best_config_list[j].is_equal(config):
                return False;
        return True;

    def __check_for_error(self,config):
        ontological_generators = config.get_ontological_generators()
        for g in ontological_generators:
            for bond in g.get_outbonds():
                if bond.get_connector() != None:
                    q = config.get_generator_by(bond.get_connector())
                    if not q:
                        config.print_info()
                        print 'In Configuration.py: check error in configuration connectivity.',repr(q)
                        exit(1)


    # input: initial configuration, # of iterations, simulated annealing initial temperature
    # returns the best configuration
    def mcmc_simulated_annealing_inference(self, input_name, number_of_iterations, global_jump_config, output_path,
                                           feature_support_thresh=.5, dynamic_inference=False, with_temporal_bonds=False,
                                           top_k=3, c_i=None):

        # if there are no
        if len(global_jump_config.get_feature_generators()) < 1: return ([],[],[],[])
        #(best_config_list,best_energy_list,best_accuracies,sorted_bests)

#        if os.path.isdir(output_path + '/best') == False:
#            os.system('mkdir ' + output_path + '/best')

        #if os.path.isdir(output_path + '/accepted') == False:
        #    os.system('mkdir ' + output_path + '/accepted')

        #print 'output path in mcmc: ',output_path
        if os.path.isdir(output_path + '/proposed') == False:
            os.system('mkdir -p ' + output_path + '/proposed')

        #accepted_results_path = output_path + '/accepted'
        proposed_results_path = output_path + '/proposed'
#        best_results_path = output_path + '/best'

        accepted_profile_filename = output_path + '/' + input_name + '_energy_accepted.csv'
        accepted_profile_file = open(accepted_profile_filename,'w')

#        proposed_profile_filename = output_path + '/' + input_name + '_proposed.csv'
#        proposed_profile_file = open(proposed_profile_filename,'w')

#        best_profile_filename = output_path + '/' + input_name + '_best.csv'
#        best_profile_file = open(best_profile_filename,'w')

        # Read the number of iterations
        N = number_of_iterations

        #if not dynamic_inference:
        #    global_jump_config = self.create_global_jump_configuration()

        # Randomly sample a initial configuration if none is passed
        if c_i == None:
#            print '@ Setting initial configuration.'
            c_i = self.global_proposal.propose(global_jump_config, with_temporal_bonds, feature_support_thresh) #,'best')


#        print 'INITIAL CONFIGURATION'
        c_i.print_info()
#        os.system("read -p 'pause'")

        accuracy_score = self.get_accuracy_score(c_i)

        # Set the current configuration to be the initial configuration
        current_c = c_i
        current_energy = c_i.get_energy(self.__bond_weights)

        # Set the best configuration to be the initial configuration
        best_c = c_i.get_copy()
        best_energy = current_energy

        best_config_list = [best_c]
        best_energy_list = [best_energy]
        best_score_list = [accuracy_score]
        worst_best_config_index = 0

        proposed_config_file = proposed_results_path + '/0.txt'
#--        self.save_configuration(proposed_config_file, current_c)

#       proposed_profile_file.write(repr(current_energy)+','+repr(min(best_energy_list))+','+repr(accuracy_score)+',i\n')
        accepted_profile_file.write(repr(current_energy)+','+repr(min(best_energy_list))+','+repr(accuracy_score)+',i\n')

        # Initially, there is no new configuration
        new_c = None

        # set simulated annealing params
        # K = 3500
        T0 = N # K * 0.8
        alpha = float('0.' + '9' * (len(str(N))-1) ) # 0.9966666666

        # start inference process
        for i in range(N):
            T = T0 * math.pow(alpha,i)

            # Randomly sample a number between 0 and 1 to be the probability of choosing one move or other
            move_chance = random.uniform(0,1)

            # Select a move given the sampled probability value
            if not dynamic_inference:
                if move_chance <= self.__global_proposal_chance:
                    # Get a new configuration using the global proposal distribution
                    print '@ ITERATION #'+repr(i)+': global proposal jump'
                    new_c = self.global_proposal.propose(global_jump_config, feature_support_thresh, with_temporal_bonds)
                    #new_c.print_info()
                else:
                    # Get a new configuration using a local proposal distribution
                    #print '@ ITERATION #'+repr(i)+': local proposal -- generator replacement based on best k candidates'
                    z = random.uniform(0,1);
                    if z <= 1.0: # 0.8:
                        print '@ ITERATION #'+repr(i)+': local proposal -- generator replacement based on best k candidates'
                        selection_type = 'level'
                        new_c = self.local_proposal.propose(current_c, with_temporal_bonds, selection_type,
                                                            feature_support_thresh)
                        #new_c.print_info()
                    elif z <= 1.0:
                        print '@ ITERATION #'+repr(i)+': local proposal -- add new generator to open bond'
                        new_c = self.local_proposal.add_remove_generator(current_c); #, feature_thresh=feature_support_thresh);
                    else:
                        #print '@ ITERATION #'+repr(i)+': local proposal -- propose interaction'
                        new_c = self.local_proposal.apply_spatial_coherence(current_c)
                        #new_c = self.local_proposal.propose_interaction_generator(current_c) #, from_level=3)
                        #new_c.print_info()
            else:
                if move_chance < self.__global_proposal_chance:
                    print '@ ITERATION #'+repr(i)+': regular local proposal - generator replacement based on best k candidates'
                    selection_type = 'level'
                    new_c = self.local_proposal.propose(current_c, with_temporal_bonds, selection_type,
                                                        feature_support_thresh)
                else:
                    print '@ ITERATION #'+repr(i)+': time-based local proposal'
                    new_c = self.local_proposal.time_based_propose(current_c, current_c.get_current_time())

            #self.__check_for_error(new_c)

            #print 'NEW CONFIGURATION'
            #new_c.print_info()

            #print 'new configuration length: ',len(new_c.get_ontological_generators()),' + ',len(new_c.get_feature_generators())

            # Compute the energy of the new configuration
            new_energy = new_c.get_energy(self.__bond_weights)
            print 'current config\'s energy: ',current_energy,' new config\'s energy: ',new_energy

            # Compute the log of the probability to change from the current configuration to the newly sampled configuration
            #p = -(new_energy-current_energy)/T;
            log_p = math.exp(-(new_energy-current_energy)/T);

            # Randomly sample a number from a uniform distribution to determine whether the newly sampled configuration should be accepted or not
            log_z = random.uniform(0,1); #math.log(random.uniform(0,1),math.exp(1))

            # Accept the new configuration if the condition is satisfied
            print 'log(p)=' + repr(log_p) + ' > log(z)=' + repr(log_z) + '?'

            if new_energy < current_energy or log_p > log_z:
                print 'ACCEPTED' # For the cases when the local proposal returns the same configuration -- when it fails to suggest a new one

                print '@ Old Configuration:'
                current_c.print_info()

                if current_c != new_c:
                    self.dispose_configuration(current_c)

                current_c = new_c
                current_energy = new_energy

#                accuracy_score = self.get_accuracy_score(current_c)
                print '@ Newly Accepted Configuration:'
                current_c.print_info()

                # if top_k > 1:
                if len(best_config_list) < top_k:
                    if self.__not_in_the_list(new_c, best_config_list):
                        print 'List not full, add new config to the list'
                        best_config_list.append(new_c.get_copy())
                        best_energy_list.append(new_energy)
                        best_score_list.append(accuracy_score)
                        if new_energy > best_energy_list[worst_best_config_index]:
                            worst_best_config_index = len(best_energy_list)-1

                elif new_energy < best_energy_list[worst_best_config_index] and \
                        self.__not_in_the_list(new_c, best_config_list): # and new_energy not in best_energy_list:

                    print 'Energy is smaller than one of the configs in the list, REMOVE and ADD';

                    # discard the worst configuration in the list
                    worst_best_config = best_config_list[worst_best_config_index]
                    del best_config_list[worst_best_config_index]
                    del best_energy_list[worst_best_config_index]
                    del best_score_list[worst_best_config_index]
                    self.dispose_configuration(worst_best_config)

                    # add newly accepted configuration
                    best_config_list.append(current_c.get_copy())
                    best_energy_list.append(current_energy)
                    best_score_list.append(accuracy_score)

                    bests = []
                    for t in range(len(best_config_list)):
                        bests.append((best_config_list[t],best_energy_list[t]))

                    sorted_bests = sorted(bests, key=lambda x: x[1], reverse=True)
                    worst_best_config_index = best_config_list.index(sorted_bests[0][0])

                    print 'INSIDE: sorted bests', repr(sorted_bests);

                    del bests
                    del sorted_bests

#                proposed_profile_file.write(repr(new_energy)+','+repr(min(best_energy_list))+','+repr(accuracy_score)+',a\n')
            else:
                new_score = self.get_accuracy_score(new_c)
#                proposed_profile_file.write(repr(new_energy)+','+repr(min(best_energy_list))+','+repr(new_score)+',r\n')

            accepted_profile_file.write(repr(current_energy)+','+repr(min(best_energy_list))+','+repr(accuracy_score)+'\n')

#--            proposed_config_file = proposed_results_path + '/' + repr(i+1) + '.txt'
#--            self.save_configuration(proposed_config_file, current_c)

            # sort best k configurations based on their total energy
            bests = []
            for t in range(len(best_config_list)):
                bests.append((best_config_list[t], best_energy_list[t]))
            sorted_bests = sorted(bests, key=lambda x: x[1])

            print 'OUTSIDE: sorted bests', repr(sorted_bests);

#            best_profile_file.write(repr(i+1))
#            for j in range(len(sorted_bests)):
#                best_profile_file.write(','+repr(sorted_bests[j][1]))
#                best_config_save_filename = best_results_path + '/' + repr(i+1) + '_' + input_name + '_best_config_rank' + repr(j+1) + '.txt'
#                self.save_configuration(best_config_save_filename,sorted_bests[j][0])

#            best_profile_file.write('\n')

            del bests
            del sorted_bests

#       proposed_profile_file.close()
        accepted_profile_file.close()
#       best_profile_file.close()

        bests = []
        best_accuracies = []
        for t in range(len(best_config_list)):
            best_c = best_config_list[t]
            accuracy_score = self.get_accuracy_score(best_c)
            best_accuracies.append(accuracy_score)
            bests.append((best_config_list[t],best_energy_list[t]))#,accuracy_score))

        sorted_bests = sorted(bests, key=lambda x: x[1])

        # delete all *.scores files
        #os.system('rm ' + str(os.getpid()) + '*.scores')

        return (best_config_list, best_energy_list, best_accuracies, sorted_bests)

    def get_baseline_configuration(self, global_jump_config, rank=1):
        new_c = self.global_proposal.baseline_configuration(global_jump_config, rank);
#       new_c = self.global_proposal.propose(global_jump_config, 0.0, with_temporal_bonds, type='baseline');
        return new_c;

    def add_next_features(self, config, global_jump_config=None):
        current_time = config.get_current_time()
        #print 'current time: ',repr(current_time)
        if current_time < 0:
            self.__features.sort(key=lambda feature: feature.time)
            current_time = self.__features[0].time
            next_features = [ self.__features[i] for i in range(len(self.__features)) if self.__features[i].time == current_time ]
        else:
            next_time = None
            for i in range(len(self.__features)):
                if self.__features[i].time > current_time:
                    next_time = self.__features[i].time
                    break
            next_features = [ self.__features[i] for i in range(len(self.__features)) if self.__features[i].time == next_time ]

        # if there are not more features to be explained, return False to mean that no more features exist
        if not next_features:
            return False, global_jump_config

        next_time = next_features[0].time
        #print 'next time: ',next_time
        config.set_current_time(next_time)
        #os.system('read -p "pause"')
        for feature in next_features:
            #print 'feature time: ',feature.time
            if feature.time == next_time:
                g_f = MyGenerator(feature.name,self.__ontology.get_level(feature.name),
                              self.__ontology.get_modalities(feature.name),'feature',
                              feature.cost,[ feature.time ])

                bond_structure = self.__ontology.get_bond_structure(feature.name)

                g_f.set_bond_structure(bond_structure)
                g_f.set_rlocation(feature.location)
                g_f.set_feature_path(feature.path)
                g_f.set_groundtruth_label(feature.label)

                self.find_top_labels(g_f)
                top_labels = g_f.get_top_labels()
                #print 'top labels: ',repr(g_f.get_top_labels())

                config.add_generator(g_f)

                # update existing global jump configuration
                if global_jump_config == None:
                    global_jump_config = Configuration()

                global_jump_config.add_generator(g_f.get_copy())
                for i in range(len(top_labels)):
                    name = top_labels[i].name

                    g_i = MyGenerator(name,self.__ontology.get_level(name),
                                  self.__ontology.get_modalities(name),
                                  'ontological',top_labels[i].cost,[ feature.time ])

                    bond_structure = self.__ontology.get_bond_structure(name)
                    g_i.set_bond_structure(bond_structure)
                    g_i.set_rlocation(feature.location)

                    global_jump_config.add_generator(g_i)
                    top_labels[i].g_id = g_i.get_id()

        global_jump_config.set_current_time(next_time)
        # to indicate success in adding more features
        return True, global_jump_config

    def create_global_jump_configuration(self):
        c = Configuration()
        for feature in self.__features:
            g_f = MyGenerator(feature.name,self.__ontology.get_level(feature.name),
                              self.__ontology.get_modalities(feature.name),'feature',
                              feature.cost,[ feature.time ])
            print 'FIND TOP LABELS FOR', repr(feature.path);

            bond_structure = self.__ontology.get_bond_structure(feature.name)
            g_f.set_bond_structure(bond_structure)
            g_f.set_rlocation(feature.location)

            g_f.set_feature_path(feature.path)
            g_f.set_groundtruth_label(feature.label)

            box = feature.box_location
            if len(box) == 6:
                g_f.set_location(box[0],box[1],box[2],box[3],box[4],box[5])

            #bond_structure = self.__ontology.get_bond_structure(feature.name)
            #print 'Find top labels for', g_f.get_name()
            self.find_top_labels(g_f)
            c.add_generator(g_f)
            top_labels = g_f.get_top_labels()

            print 'feature: ' + g_f.get_name()
            print 'top labels: ', top_labels, '\n';
            for i in range(len(top_labels)):
                name = top_labels[i].name
                #print name
                g_i = MyGenerator(name,self.__ontology.get_level(name),
                                  self.__ontology.get_modalities(name),
                                  'ontological',top_labels[i].cost,[ feature.time ])

#                print 'feature time: ', feature.time

                g_i.set_rlocation(feature.location)

                bond_structure = self.__ontology.get_bond_structure(name)
                g_i.set_bond_structure(bond_structure)

                c.add_generator(g_i)
                top_labels[i].g_id = g_i.get_id()  # keep track of the g associated to it

        # Print configuration for debugging
        #c.print_info();
        return c

    def dispose_configuration(self, c):
        c.remove_bonds()
        del c

    # I think this function should be moved to the global proposal function
    # Find the top labels for groups of features
    def find_top_labels(self, g, k=6):
        labels = self.__ontology.get_labels()
        label_score = []
        for i in range(len(labels)):
            # put a condition that verifies if the labels is
            print labels[i] + ' -- ' + g.get_name()
            score = self.__predictor[g.get_name()].run(labels[i], g);
            label_score.append((score, labels[i]));

        #print 'feature: ' + repr(g.get_features())
#       label_score.sort(reverse=True) -- if positive numbers are desired

        # The scores are sorted in ascending order because the scores are already transformed to negative values
        label_score.sort()
        print 'labels: ' + repr(labels)
        print 'scores: ' + repr(label_score)

        #print 'scores: ' + repr(label_score)

        feature_bond_structure = self.__ontology.get_bond_structure(g.get_name())
        #print g.get_name() + ' ' + repr(feature_bond_structure)

        k = len(labels);
        for i in range(k):
            name = label_score[i][1]
            #print 'label:' + name
            # when features connect to labels
            label_modalities = self.__ontology.get_modalities(name)
            #print 'modalities: '+repr(label_modalities)
            for bond in feature_bond_structure:
                if bond[0] in label_modalities:
                    score = label_score[i][0]
                    level = self.__ontology.get_level(name)
                    modality = self.__ontology.get_modalities(name)
                    g.add_top_label(Label(name, modality, level, score, -1, 0.0))
                    break

            # when labels connect to features
#           bond_structure = self.__ontology.get_bond_structure(name)
#           for bond in bond_structure:
#               if g.get_name() in bond:
#                   score = label_score[i][0]
#                   level = self.__ontology.get_level(name)
#                   modality = self.__ontology.get_modalities(name)
#                   g.add_top_label(Label(name,modality,level,score,-1,0.0))
#                   break
            

    def __get_groundtruth_bond_map(self):
        # read connections from the ground truth file
        gt_file = open(self.__gt_filename,'r')
        line = gt_file.readline()
        data = string.split(line.replace('\n',''),',')

        number_of_generators = int(data[0])
        number_of_bonds = int(data[1])

        ids_name = {}
        gt_generator_names = []
        for j in range(number_of_generators):
            line = gt_file.readline()
            data = string.split(line.replace('\n',''),',')
            ids_name[data[0]] = data[1]
            gt_generator_names.append(data[1])

        gt_bond_map = {}
        for j in range(number_of_bonds):
            line = gt_file.readline()
            data = string.split(line.replace('\n',''),',')
            if ids_name[data[0]] not in gt_bond_map:
                gt_bond_map[ids_name[data[0]]] = []
            gt_bond_map[ids_name[data[0]]].append(ids_name[data[1]])

        gt_file.close()
        #del gt_generator_names

        return (gt_generator_names,gt_bond_map)

    def __extract_label_name(self,g_f):
        features_path = g_f.get_features()
        path_parts = string.split(features_path,'/')
        filename_parts = string.split(path_parts[len(path_parts)-1],'.')
        name_parts = string.split(filename_parts[0],'_')
        name = name_parts[2] + '_' + name_parts[3]
        return name

    def __get_label_from_id_label(self,id_label):
        data = string.split(id_label,'_')
        return data[0]

    def compute_performance_rate(self,best_configs):
        generator_true_positive_rate = []
        generator_false_positive_rate = []
        bond_true_positive_rate = []
        bond_false_positive_rate = []
        for i in range(len(best_configs)):
            generator_true_positive_rate.append(0.0)
            generator_false_positive_rate.append(0.0)
            bond_true_positive_rate.append(0.0)
            bond_false_positive_rate.append(0.0)

        # get ground truth information
        (gt_generator_names,gt_bond_map) = self.__get_groundtruth_bond_map()
        number_of_groundtruth_generators = len(gt_generator_names)
        number_of_groundtruth_bonds = len(gt_generator_names)
        for key in gt_bond_map:
            number_of_groundtruth_bonds += len(gt_bond_map[key])

        #print 'number of groundtruth bonds: ' + repr(number_of_groundtruth_bonds)

        # analyze each configuration
        for i in range(len(best_configs)):
            generators_label_map = {}

            groundtruth_generators = []
            for j in range(len(gt_generator_names)):
                label_name = self.__get_label_from_id_label(gt_generator_names[j])
                groundtruth_generators.append(label_name)

            generator_hits = 0.0

            # count the number of generators that appear in the ground truth configuration
            #print repr(groundtruth_generators)
            ontological_generators = best_configs[i].get_ontological_generators()
            for g_o in ontological_generators:
                if g_o.get_name() in groundtruth_generators:
                    generator_hits += 1.
                    g_o.set_is_match(True)
                    del groundtruth_generators[groundtruth_generators.index(g_o.get_name())]
                    #print repr(groundtruth_generators)

            generator_false_positive_rate[i] = (len(ontological_generators) - generator_hits) / len(ontological_generators)
            generator_true_positive_rate[i] = generator_hits / number_of_groundtruth_generators

            #print 'gtpr: ' + repr(generator_hits) + 'gfpr: ' + repr((len(ontological_generators) - generator_hits))

            # count the number of grounding bonds that correctly explain the features
            config_total_number_of_bonds = 0.0
            feature_generators = best_configs[i].get_feature_generators()
            for g_f in feature_generators:
                inbonds = g_f.get_inbonds()
                for bond in inbonds:
                    g_o = best_configs[i].get_generator_by(bond.get_connector(),'id')
                    generators_label_map[g_o.get_id()] = g_o.get_name()

                    # keep track of the number of bonds in the configuration
                    config_total_number_of_bonds += 1.

                    #print 'g_o:' + repr(g_o)
                    if g_o.get_name() in g_f.get_groundtruth_label():
                        if g_o.get_level() < 3:
                            generators_label_map[g_o.get_id()] = self.__extract_label_name(g_f)

                        #	print 'CHECK >> ' + g_f.get_groundtruth_label() + ' - ' + g_o.get_name()
                        label_name = generators_label_map[g_o.get_id()]
                        if label_name in gt_generator_names:
                            bond_true_positive_rate[i] += 1.

            bond_hits = 0.0

            #	        print 'generators_label_map: ' + repr(generators_label_map)
            #	        print 'gt_bond_map: ' + repr(gt_bond_map)
            #	        print 'gt_generator_names: ' + repr(gt_generator_names)

            for g_i in ontological_generators:
                outbonds = g_i.get_outbonds()
                # get name+id if it is an object
                #print 'g_i:' + repr(g_i.get_id())
                g_i_name = generators_label_map[g_i.get_id()]
                for bond in outbonds:
                    if bond.get_connector() != None:
                        g_j = best_configs[i].get_generator_by(bond.get_connector(),'id')
                        # if not a feature generator
                        if g_j.get_type() != 'feature':
                            config_total_number_of_bonds += 1.
                            g_j_name = generators_label_map[g_j.get_id()]
                            if g_i_name in gt_bond_map:
                                if g_j_name in gt_bond_map[g_i_name]:
                                    bond.set_is_match(True)
                                    bond_true_positive_rate[i] += 1.
                        else:
                            # print 'g_i label: ' + g_i.get_name() + ' g_j label: ' + repr(g_j.get_groundtruth_label())
                            if g_i.get_name() in g_j.get_groundtruth_label():
                                if g_i.get_level() < 3 and self.__extract_label_name(g_j) in gt_generator_names:
                                    # print 'OBJECT -- g_i label: ' + g_i.get_name() + ' g_j label: ' + self.__extract_label_name(g_j)
                                    bond.set_is_match(True)
                                elif g_i.get_level() > 2:
                                    # print 'ACTION -- g_i label: ' + g_i.get_name() + ' g_j label: ' + repr(g_j.get_groundtruth_label())
                                    bond.set_is_match(True)


            bond_hits = bond_true_positive_rate[i]
            bond_false_positive_rate[i] = (config_total_number_of_bonds - bond_true_positive_rate[i]) / config_total_number_of_bonds
            bond_true_positive_rate[i] /= number_of_groundtruth_bonds

        #	        print 'btpr: ' + repr(bond_hits) + 'bfpr: ' + repr((config_total_number_of_bonds - bond_true_positive_rate[i]))

        gtpr = 0.0
        btpr = 0.0
        gfpr = 0.0
        bfpr = 0.0
        for i in range(len(best_configs)):
            gfpr += generator_false_positive_rate[i]
            gtpr += generator_true_positive_rate[i]
            bfpr += bond_false_positive_rate[i]
            btpr += bond_true_positive_rate[i]
        gtpr /= 3.
        gfpr /= 3.
        btpr /= 3.
        bfpr /= 3.

        return (gtpr,gfpr,btpr,bfpr)

    def get_top_k_accuracy_score(self,best_configs):
        feature_generators = best_configs[0].get_feature_generators()
        total = len(feature_generators)

        (gt_generator_names,gt_bond_map) = self.__get_groundtruth_bond_map()
        # total_number_generators_from_main_activity = total_generators_number
        total_generators_number = len(gt_generator_names)

        global_acc_count = 0.0
        global_tp_count = []
        global_bond_count = []
        total_bond_count = 0.0
        total = total_generators_number
        for i in range(total_generators_number):
            global_tp_count.append(0.0)

        for i in range(len(best_configs)):
            global_bond_count.append(0.0)

        for i in range(len(best_configs)):
            generators_label_map = {}

            #			count = 0.0
            #			print 'STATUS >> GROUNDTRUTH LABEL - PREDICTED LABEL'
            feature_generators = best_configs[i].get_feature_generators()
            ontological_generators = best_configs[i].get_ontological_generators()
            for g_f in feature_generators:
                inbonds = g_f.get_inbonds()
                for bond in inbonds:
                    g_o = best_configs[i].get_generator_by(bond.get_connector(),'id')
                    generators_label_map[g_o.get_id()] = g_o.get_name()
                    #print 'g_o:' + repr(g_o)
                    if g_o.get_name() in g_f.get_groundtruth_label():
                        # just to get the obj_name+obj_id from the original annotation
                        if g_o.get_level() < 3:
                            generators_label_map[g_o.get_id()] = self.__extract_label_name(g_f)

                        #						print 'CHECK >> ' + g_f.get_groundtruth_label() + ' - ' + g_o.get_name()
                        label_name = generators_label_map[g_o.get_id()]
                        if label_name in gt_generator_names:
                            #							count += 1.0
                            g_o.set_is_match(True)
                            #							global_tp_count[feature_generators.index(g_f)] += 1.0
                            global_tp_count[gt_generator_names.index(label_name)] += 1.0
                            global_acc_count += 1.0
                        #					else:
                        #						print 'WRONG >> ' + g_f.get_groundtruth_label() + ' - ' + g_o.get_name()

            bond_hits = 0.0
            total_bonds = 0.0
            for g_i in ontological_generators:
                outbonds = g_i.get_outbonds()
                g_i_name = generators_label_map[g_i.get_id()]
                for bond in outbonds:
                    if bond.get_connector() != None:
                        g_j = best_configs[i].get_generator_by(bond.get_connector(),'id')
                        if g_j.get_type() != 'feature':
                            total_bonds += 1
                            g_j_name = generators_label_map[g_j.get_id()]
                            if g_i_name in gt_bond_map:
                                if g_j_name in gt_bond_map[g_i_name]:
                                    bond.set_is_match(True)
                                    bond_hits += 1.0

            global_bond_count[i] = bond_hits
            total_bond_count += total_bonds

        # computing true positive rates
        k = len(best_configs)
        global_tp_rate = 0.0
        for i in range(total):
            if global_tp_count[i] > 0.0:
                global_tp_count[i] = 1. #/= k
            global_tp_rate += global_tp_count[i]
        global_tp_rate /= total

        global_acc_rate = global_acc_count / (k*total)

        bond_count_rate = 0.0
        for i in range(k):
            bond_count_rate += global_bond_count[i]
        if (total_bond_count > 0):
            bond_count_rate /= total_bond_count

        return (global_acc_rate, global_tp_rate, 1.-global_tp_rate,bond_count_rate,1.-bond_count_rate)
			
#	def get_accuracy_score(self,config):
#		feature_generators = config.get_feature_generators()
#		
#		generators_label_map = {}
#		(gt_generator_names,gt_bond_map) = self.__get_groundtruth_bond_map()
#		
#		# total_number_generators_from_main_activity = total_generators_number
#		total = len(gt_generator_names)
#		
#		energy = config.get_energy(self.__bond_weights)
#		
#		print 'gt_generator_names: ' + repr(gt_generator_names)
#		
#		count = 0.0
##		print 'STATUS >> GROUNDTRUTH LABEL - PREDICTED LABEL'
#		for g_f in feature_generators:
#			inbonds = g_f.get_inbonds()
#			for bond in inbonds:
#				g_o = config.get_generator_by(bond.get_connector(),'id')
#				generators_label_map[g_o.get_id()] = g_o.get_name()
#				if g_o.get_name() in g_f.get_groundtruth_label():
#					print 'CHECK >> ' + repr(g_f.get_groundtruth_label()) + ' - ' + g_o.get_name() 
#					if g_o.get_level() < 3:			
#						generators_label_map[g_o.get_id()] = self.__extract_label_name(g_f)
#						
##					print 'CHECK >> ' + g_f.get_groundtruth_label() + ' - ' + g_o.get_name() 
#					label_name = generators_label_map[g_o.get_id()]
#					if label_name in gt_generator_names:
#						g_o.set_is_match(True)
#						count += 1.0
#				else:	
#					print 'WRONG >> ' + repr(g_f.get_groundtruth_label()) + ' - ' + g_o.get_name()
#		
#		print 'count: ' + repr(count) + ' total: ' + repr(total) + ' energy: ' + repr(energy)
#		return (count/total)

    def concepts_score_hits(self,config):
        feature_generators = config.get_feature_generators()
        total = len(feature_generators)
        gt_concepts = [] # gather all concepts in the ground truth configuration
        #print 'total ' + repr(total)
        for g_f in feature_generators:
            #print 'g_f: ' + repr(g_f.get_groundtruth_label())
            for concept in g_f.get_groundtruth_label():
                gt_concepts.append(concept)
        count = 0.0
        #print 'gt_concepts: ' + repr(gt_concepts)
        # this counting of concept hits does not take into account
        for g_f in feature_generators:
            inbonds = g_f.get_inbonds()
            for bond in inbonds:
                g_o = config.get_generator_by(bond.get_connector(),'id')
                if g_o.get_name() in gt_concepts:
                    # if there are repeated elements, only the first in the list will be removed
                    gt_concepts.remove(g_o.get_name())
                    #print 'gt_concepts: ' + repr(gt_concepts)
                    #g_o.set_is_match(True)
                    count += 1.0
        score = count/total
        if score > 1.0:
            score = 1.0
        return score

    def get_accuracy_score(self,config):
        feature_generators = config.get_feature_generators()
        total = len(feature_generators)
        count = 0.0
        #		print 'STATUS >> GROUNDTRUTH LABEL - PREDICTED LABEL'
        for g_f in feature_generators:
            inbonds = g_f.get_inbonds()
            for bond in inbonds:
                g_o = config.get_generator_by(bond.get_connector(),'id')
                if g_o.get_name() in g_f.get_groundtruth_label():
                    #					print 'CHECK >> ' + repr(g_f.get_groundtruth_label()) + ' - ' + g_o.get_name()
                    g_o.set_is_match(True)
                    count += 1.0
                #				else:
                #					print 'WRONG >> ' + repr(g_f.get_groundtruth_label()) + ' - ' + g_o.get_name()
        return (count/total)
