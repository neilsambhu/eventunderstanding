#!/usr/bin/python

# only import if Generator is customized
from MyGenerator import * 

from Configuration import *
from ProposalDistribution import *

import math
import random
import numpy


class LocalProposal(ProposalDistribution):

    def __init__(self,ontology,predictor,bond_weights=None,strict_mode=True,time_unit=1,k=3):
        super(LocalProposal,self).__init__(ontology,predictor)
        self.__ont_w = 0.01 # prev set as .01
        self.__k = k
        self.__ontology = ontology
        self.__predictor = predictor
        self.__bond_weights = bond_weights
        self.__strict_mode = strict_mode
        self.__time_unit = time_unit
        #self.__feature_thresh = feature_support_thresh

    #	def __init__(self,method,feature,k=3):
    #		super(LocalProposal,self).__init__(method,feature)
    #		self.__k = k

    def __intersect(self,list_a,list_b):
        return list(set(list_a) & set(list_b))

    def __discard_configuration(self,config):
        config.remove_bonds()
        config.remove_generators()
        del config

    def __probabilistic_candidate_selection(self, candidate_local_energies):
        # compute the probability of each candidate based on their local energy contributions
        prob = []
        sum = 0.0
        for energy in candidate_local_energies:
            sum += abs(energy)
            prob.append(1.0 * abs(energy))

        if sum > 0.0:
            # compute the probability of each candidate given their locally contributed energies
            #print 'energies:',repr(prob)
            for i in range(len(prob)):
                prob[i] = prob[i] / sum

            #print 'prob:',repr(prob)

            # sample a candidate with a certain probability
            result = numpy.random.multinomial(1, prob)
            #print 'result',repr(result)

            # get the index of the selected candidate (the one of minimum energy...)
            #print 'list',repr(result.tolist())
            candidate_index = result.tolist().index(1)
            #print 'selected index:',candidate_index

            # free memory
            del prob
            del result

            # return index of the selected candidate
            return candidate_index
        else:
            return random.randrange(len(prob))

    def __construct_new_configuration(self, config, candidates, feature_generator):
        # follow similar idea of function below...
        candidate_configs = []
        candidate_generators = []

        feature_generator.get_time().sort()
        current_time = feature_generator.get_time()[-1]

        for i in range(len(candidates)):
            # collect all data to create a generator
            label_name = candidates[i]
            level = self.__ontology.get_level(label_name)
            modalities = self.__ontology.get_modalities(label_name)
            bond_structure = self.__ontology.get_bond_structure(label_name)

            # name,level,modality,type,cost,time
            ontological_generator = MyGenerator(label_name, level, modalities, 'ontological', 0, [ current_time ])

            # set feature location associated to the new candidate
            ontological_generator.set_rlocation(feature_generator.get_rlocation())

            # define the bond structure of the generator here
            ontological_generator.set_bond_structure(bond_structure)

            # create a new configuration in which the new candidate replaces the one to be remove
            new_config = config.get_copy()
            new_config.add_generator(ontological_generator)

            candidate_generators.append(ontological_generator)

            # make changes to the connection of the new configuration given the newly added generator
            #self.__update_bonds_after_replacement(new_config, g_f, g_c)
            self.__place_support_bonds(feature_generator, ontological_generator, new_config)
            self.__place_ontological_bonds(ontological_generator, new_config)

            # record newly proposed configs with
            candidate_configs.append(new_config)

        # account for temporal bonds linking to the past
        for i in range(len(candidate_generators)):
            self.__place_past_ontological_bonds(candidate_generators[i], candidate_configs[i], current_time)

        # account for temporal connections linking to the future
        #for i in range(len(candidate_generators)):
        #    self.__place_future_ontological_bonds(candidate_generator[i],candidate_configs[i],current_time)

        # compute local energy contributions by new candidates configuration
        candidate_local_energies = []
        for i in range(len(candidate_generators)):
            # get local energy that is being contributed by new
            local_energy = candidate_configs[i].get_local_energy(candidate_generators[i],self.__bond_weights)
            candidate_local_energies.append(local_energy)

        # select a candidate according to probability computed based on their locally contributed energy
        candidate_index = self.__probabilistic_candidate_selection(candidate_local_energies)

        # update the current configuration to the new one
        #self.__discard_configuration(config) # check if the upper code is making a copy of this configuration for other purposes
        new_config = candidate_configs[candidate_index]

        # discard temporary configurations, and others...
        del candidate_configs[candidate_index]
        for i in range(len(candidate_configs)):
            self.__discard_configuration(candidate_configs[0])

        return new_config

    def time_based_propose(self,config,current_time):
        # probability of maintaining the same explanation
        change_explanation = True
        same_state_prob = 0.3
        if random.uniform(0, 1) < same_state_prob:
            change_explanation = False

        feature_generators = config.get_feature_generators()

        newly_added_feature_generators = []
        past_feature_generators = []
        past_feature_generator_connectors = {}
        past_inbond_labels = []
        for feature_generator in feature_generators:
            if self.__intersect(feature_generator.get_time(),[current_time]) :
                newly_added_feature_generators.append(feature_generator)
            elif self.__intersect(feature_generator.get_time(),[current_time - self.__time_unit]):
                past_feature_generators.append(feature_generator)
                # used to know to which ontological generator to connect
                # (case when aiming at keeping the same explanation for the new feat generators)
                past_feature_generator_connectors[feature_generator.get_id()] = []
                for bond in feature_generator.get_outbonds():
                    # check to which one it is
                    if bond.get_connector() != None:
                        #past_feature_generator_connectors[feature_generator.get_id()].append(bond)
                        if bond.get_value() not in past_feature_generator_connectors:
                            past_feature_generator_connectors[bond.get_value()] = []
                        past_feature_generator_connectors[bond.get_value()].append((feature_generator,bond))

                for bond in feature_generator.get_inbonds():
                    #coordinate = bond.get_connector_coordinate()
                    ontological_generator = config.get_generator_by(bond.get_connector())
                    past_inbond_labels.append(ontological_generator.get_name())
                    #outbond = ontological_generator.get_outbond_by_coordinate(coordinate)
                    #past_labels.append()

        #print len(newly_added_feature_generators),' newly added features: ',repr(newly_added_feature_generators)
        #print len(past_feature_generators),' past feature generators: ',repr(past_feature_generators)
        #print len(past_inbond_labels),' past inbond labels: ',repr(past_inbond_labels)

        #any_feature = newly_added_feature_generators[random.randrange(len(newly_added_feature_generators))]
        if not past_feature_generators and not past_inbond_labels and not len(config.get_ontological_generators()):
            for feature_generator in newly_added_feature_generators:
                top_labels = feature_generator.get_top_labels()
                index = random.randrange(len(top_labels))
                label = top_labels[index]

                #print 'feature: ' + g_f.get_name()
                #print ' top labels: '

                #print 'selected label: ',label.name
                #print 'level: ',self.__ontology.get_level(label.name)
                ontological_generator = MyGenerator(label.name, self.__ontology.get_level(label.name),
                                                    self.__ontology.get_modalities(label.name), 'ontological',
                                                    label.cost, [current_time])

                #print 'feature time: ', feature.time
                ontological_generator.set_rlocation(feature_generator.get_rlocation())

                bond_structure = self.__ontology.get_bond_structure(label.name)
                ontological_generator.set_bond_structure(bond_structure)

                config.add_generator(ontological_generator)
                self.__place_support_bonds(feature_generator, ontological_generator, config)

                #print 'ontological generators ',len(config.get_ontological_generators())
                self.__place_ontological_bonds(ontological_generator, config)

            return config

        if not change_explanation:
            new_ontological_generators = []
            for feature_generator in newly_added_feature_generators:
                #print 'feature id: ',feature_generator.get_id(),' feature name: ',feature_generator.get_name()

                # for when feature generators's outbonds connect to ontological generators's inbonds
                for bond in feature_generator.get_outbonds():
                    #print 'out of outbond connections...'
                    # if current generator can connect to existing concepts already explaining past features
                    if bond.get_value() in past_feature_generator_connectors: # escolher a mesma configuracao ou uma nova dada certa probabilidade
                        # find out what the concept is
                        past_bond = past_feature_generator_connectors[bond.get_value()][1]
                        if bond.get_connector() != past_bond.get_connector():
                            if bond.get_connector() != None:
                                config.remove_generator(bond.get_connector())
                            ontological_generator = config.get_generator_by(past_bond.get_connector())
                            ontological_generator.get_time().append(current_time)
                            self.__place_support_bonds(feature_generator, ontological_generator, config)

                # for when ontological generators's outbonds connect to feature generators's inbonds
                context_labels = []
                for label in past_inbond_labels:
                    bond_structure = self.__ontology.get_bond_structure(label)

                    for bond in bond_structure:
                        bond_value = bond[0]
                        if self.__intersect([ bond_value ], feature_generator.get_modality()):
                            context_labels.append(label)

                if context_labels:
                    #print 'out of inbond connections...'
                    label = context_labels[random.randrange(len(context_labels))]
                    level = self.__ontology.get_level(label)
                    modalities = self.__ontology.get_modalities(label)

                    ontological_generator = MyGenerator(label, level, modalities, 'ontological', 0, [ current_time ])
                    ontological_generator.set_rlocation(feature_generator.get_rlocation())

                    bond_structure = self.__ontology.get_bond_structure(label)
                    ontological_generator.set_bond_structure(bond_structure)

                    # remove old explanation if it exists before proposing a new one
                    #print 'before - number of inbonds: ',len(feature_generator.get_inbonds())
                    #config.print_info()

                    connectors = []
                    for inbond in feature_generator.get_inbonds():
                        connectors.append(inbond.get_connector())
                        #print 'remove connector ',inbond.get_connector()
                    for generator_id in connectors:
                        config.remove_generator(generator_id)
                    del connectors
                    #print 'after - number of inbonds: ',len(feature_generator.get_inbonds())

                    config.add_generator(ontological_generator)
                    new_ontological_generators.append(ontological_generator)

                    self.__place_support_bonds(feature_generator, ontological_generator, config)
                    #print 'after connecting new generator: ',len(feature_generator.get_inbonds())
                    #config.print_info()
                    self.__place_ontological_bonds(ontological_generator, config)

                    # move to explain the next feature generator
                    #past_inbond_labels.remove(label)
                    #break

            #for generator in new_ontological_generators:

            return config

#        print 'NEW EXPLANATIONS BASED ON THE PAST'
        # if new feature are to receive new explanations based on the past
        new_ontological_generators = []
        for feature_generator in newly_added_feature_generators:
            # for when feature generators's outbonds connect to ontological generators's inbonds
            for bond in feature_generator.get_outbonds():
                # if current generator can connect to existing concepts already explaining past features
                if bond.get_value() in past_feature_generator_connectors:
                    # find out what the concept is
                    past_bond = past_feature_generator_connectors[bond.get_value()][1]
                    generator_id = past_bond.get_connector()
                    g_k = config.get_generator_by(generator_id)

                    # find out the exact interaction
                    # this can be later resolved by having a composite generator that has a name that combines one or more
                    # generators (that will be easier to implement and faster -- only thought of this now)
                    label = g_k.get_name() #self.__get_interaction_name(g_k,config)

                    # choose probabilistically whether to propose new explanations for the newly added features
                    # or to make them explain the current configuration state
#                    conditional_cooccurrences = self.__ontology.conditional_cooccurrence('interactions_'+bond.get_value(),label,True,order=1)

                    conditional_cooccurrences = self.__ontology.conditional_cooccurrence(bond.get_value()+'_'+bond.get_value(),label,True,order=1)

                    labels = conditional_cooccurrences.keys()
                    label_counts = conditional_cooccurrences.values()
                    label_index = self.__probabilistic_candidate_selection(label_counts)
                    candidates = [ labels[label_index] ]
                else:
                    # get all candidate labels
                    labels = self.__ontology.get_equivalent_labels(bond.get_value())
                    # select candidates uniformly random
                    candidates = random.sample(labels,max(self.__k,len(labels)))
                    del labels

                self.__construct_new_configuration(config,candidates,feature_generator)

            # for when ontological generator's outbonds connect to feature generators's inbonds
            #connect = False
            context_labels = []
            for label in past_inbond_labels:
                bond_structure = self.__ontology.get_bond_structure(label)

                for bond in bond_structure:
                    bond_value = bond[0]
                    if self.__intersect([ bond_value ], feature_generator.get_modality()):
                        context_labels.append(label)
                        #connect = True

            if context_labels:
                label = context_labels[random.randrange(len(context_labels))]
                level = self.__ontology.get_level(label)
                #print 'level: ',repr(level)
                modality = ''
                if level == 3:
                    modality = 'actions'
                elif level == 2:
                    modality = 'objects'

                #print 'modality: ',modality
                conditional_cooccurrences = self.__ontology.conditional_occurrence(modality+'_'+modality, label,
                                                                                   True, order=1)
                labels = conditional_cooccurrences.keys()
                #print 'labels: ',repr(labels)

                label_counts = conditional_cooccurrences.values()
                index = self.__probabilistic_candidate_selection(label_counts)
                next_label = labels[index]

                level = self.__ontology.get_level(next_label)
                modalities = self.__ontology.get_modalities(next_label)
                bond_structure = self.__ontology.get_bond_structure(next_label)

                ontological_generator = MyGenerator(next_label, level, modalities, 'ontological', 0, [ current_time ])
                ontological_generator.set_rlocation(feature_generator.get_rlocation())
                ontological_generator.set_bond_structure(bond_structure)

                config.add_generator(ontological_generator)
                new_ontological_generators.append(ontological_generator)

                # remove old explanation if it exists before proposing a new one
                #print 'before - number of inbonds: ',len(feature_generator.get_inbonds())
                #config.print_info()
                connectors = []
                for inbond in feature_generator.get_inbonds():
                    connectors.append(inbond.get_connector())
                    #print 'remove connector ',inbond.get_connector()
                for generator_id in connectors:
                    config.remove_generator(generator_id)
                del connectors
                #print 'after - number of inbonds: ',len(feature_generator.get_inbonds())


                self.__place_support_bonds(feature_generator, ontological_generator, config)
                #config.print_info()

                #print 'after connecting new generator: ',len(feature_generator.get_inbonds())
                self.__place_ontological_bonds(ontological_generator, config)

                # move to explain the next feature generator
                #past_inbond_labels.remove(label)
                #break

        # account for temporal bonds linking to the past

        for generator in new_ontological_generators:
            self.__place_past_ontological_bonds(generator, config, current_time)

        return config

    def __get_interaction_name(self,g_k,config):
        label = g_k.get_name()
        if g_k.get_level() == 3:
            connected_objects = []
            for outbond in g_k.get_outbonds():
                if outbond.get_connector() != None:
                    g_t = config.get_generator_by(outbond.get_connector())
                    if g_t.get_level() == g_k.get_level()-1:
                        connected_objects.append(g_t.get_name())
            label += '_' + connected_objects[random.sample(len(connected_objects),1)[0]]
            del connected_objects
        elif g_k.get_level() == 2:
            for inbond in g_k.get_inbonds():
                # if an inbond exists, then there is a connector (the same is not true for outbonds)
                g_t = config.get_generator_by(inbond.get_connector())
                if 'actions' in g_t.get_modality():
                    label = g_t.get_name() + '_' + label
                    break
        return label

    def __mean(self,values):
        m_i = 0.0
        n = 0
        for key in values:
            m_i += values[key]
            n += 1.0
        return m_i / n

    def compute_ontological_bond_weight(self,g_i,g_j,config,time_based_bond=False):
        label_i = g_i.get_name()
        label_j = g_j.get_name()

        #print 'try a bond between ' + label_i + ' ' + label_j

        n_ij = 0.0
        validity = False
        if time_based_bond:
            n_ij,validity = self.__ontology.time_based_prior(label_i,label_j)
        else:
            n_ij,validity = self.__ontology.prior(label_i,label_j)

        #print 'n_ij',n_ij,'validity',validity

        return -n_ij,validity

    # assume that g_k is being treated for time 'current_time'
    def __place_ontological_bonds(self,g_k,config):
        time_based_bond = False
        # close bonds between ontological generators
        ontological_generators = config.get_ontological_generators()
        #print 'ontological generators in place_ontological_bonds: ',repr(ontological_generators)
        for g_j in ontological_generators:
            if g_k.get_id() != g_j.get_id():
                # temporal connections could be treated in a higher level layer where those are weighed or here
                # if g_k.get_time() == g_j.get_time():
                if self.__intersect(g_k.get_time(),g_j.get_time()):
 #                   print 'same time? ',g_k.get_time(),' ',g_j.get_time()
                    # if ontology.obeys_constraints(g_b.get_name() ,g_j.get_name())
                    #score = self.__ontology.gprior(g_k,g_j)
                    score,valid = self.compute_ontological_bond_weight(g_k,g_j,config,time_based_bond)
                    if not valid:
                        score,valid = self.compute_ontological_bond_weight(g_k,g_j,config,time_based_bond)
                    energy = self.compute_energy(score, self.__ont_w)
#                   print 'bonding g_k(',g_k.get_name(),') and g_j(',g_j.get_name(),'), weight = ',score,', energy = ',energy
                    # try connections in both directions, whichever works
                    if config.close_bonds(g_k.get_id(), g_j.get_id(), energy, time_based_bond, self.__strict_mode) == False:
                        config.close_bonds(g_j.get_id(), g_k.get_id(), energy, time_based_bond, self.__strict_mode)

    def __place_local_ontological_bonds(self,g_k,config,local_time):
        time_based_bond = False
        # close bonds between ontological generators
        ontological_generators = config.get_ontological_generators()
        for g_j in ontological_generators:
            if g_k.get_id() != g_j.get_id():
                # temporal connections could be treated in a higher level layer where those are weighed or here
                # if g_k.get_time() == g_j.get_time():
                if self.__intersect(g_k.get_time(), [ local_time ]) and self.__intersect([ local_time ], g_j.get_time()):
                    #                   print 'same time? ',g_k.get_time(),' ',g_j.get_time()
                    # if ontology.obeys_constraints(g_b.get_name() ,g_j.get_name())
                    #score = self.__ontology.gprior(g_k,g_j)
                    score,valid = self.compute_ontological_bond_weight(g_k,g_j,config,time_based_bond)
                    if not valid:
                        score,valid = self.compute_ontological_bond_weight(g_k,g_j,config,time_based_bond)
                    energy = self.compute_energy(score, self.__ont_w)
                    #                   print 'bonding g_k(',g_k.get_name(),') and g_j(',g_j.get_name(),'), weight = ',score,', energy = ',energy
                    # try connections in both directions, whichever works
                    if config.close_bonds(g_k.get_id(),g_j.get_id(),energy,time_based_bond,self.__strict_mode) == False:
                        config.close_bonds(g_j.get_id(),g_k.get_id(),energy,time_based_bond,self.__strict_mode)

    def __place_past_ontological_bonds(self,g_k,config,current_time):
        time_based_bond = True
        ontological_generators = config.get_ontological_generators()
        for g_j in ontological_generators:
            if g_k.get_id() != g_j.get_id(): # to avoid loop connections
                if self.__intersect(g_j.get_time(),[current_time - self.__time_unit]):
 #                   print 'different times? ',g_k.get_time(),' ',g_j.get_time()
                    #score = self.__ontology.gtime_based_prior(g_j,g_k)
                    score,valid = self.compute_ontological_bond_weight(g_j,g_k,config,time_based_bond)
                    if valid:
#                        print 'score: ',score
                        energy = self.compute_energy(score, self.__ont_w)
#                       print 'bonding g_j(',g_j.get_name(),') and g_k(',g_k.get_name(),'), weight = ',score,', energy = ',energy
                        config.close_bonds(g_j.get_id(),g_k.get_id(),energy,time_based_bond,self.__strict_mode)


    def __place_future_ontological_bonds(self,g_k,config,current_time):
        time_based_bond = True
        ontological_generators = config.get_ontological_generators()
        # future connections
        for g_j in ontological_generators:
            if g_k.get_id() != g_j.get_id():
                if self.__intersect(g_j.get_time(), [current_time + self.__time_unit]):
#                    print 'different times? ',g_k.get_time(),' ',g_j.get_time()
                    #score = self.__ontology.gtime_based_prior(g_k,g_j)
                    score,valid = self.compute_ontological_bond_weight(g_k, g_j, config, time_based_bond)
                    if valid:
                        energy = self.compute_energy(score, self.__ont_w)
#                       print 'bonding g_k(',g_k.get_name(),') and g_j(',g_j.get_name(),'), weight = ',score,', energy = ',energy
                        config.close_bonds(g_k.get_id(),g_j.get_id(),energy,time_based_bond,self.__strict_mode)


    def __place_support_bonds(self, g_f, g_o, config, feature_thresh):
        time_based_bond = False
        score = self.__predictor.run(g_o.get_name(),g_f)
        score = self.thresh_function(score,feature_thresh)             # adjusting score to take positive values when needed
        energy = self.compute_energy(-score, 2.0)
        print 'bonding g_f(',g_f.get_name(),') and g_o(',g_o.get_name(),'), weight = ',score,', energy = ',energy
        if config.close_bonds(g_f.get_id(), g_o.get_id(), energy, time_based_bond, self.__strict_mode) == False:
            print 'did not connect'
            config.close_bonds(g_o.get_id(), g_f.get_id(), energy, time_based_bond, self.__strict_mode)
        else:
            if (g_f.get_name() == 'hof' and g_o.get_name() == 'butter-o') or (g_f.get_name() == 'hog' and g_o.get_name() == 'butter-a'):
                print 'bonding g_f(', g_f.get_name(), ') and g_o(', g_o.get_name(), '), weight = ', \
                        score, ', energy = ', energy
                exit(1)


    # composite generator will happen in activity proposal
    # implementation will now look for an ontological generator to be replaced
    # then, all feature connections (get them by inbonds) will be updated

    def __find_interactions(self, root_generator, config):
        stack = []
        discovered = {}
        stack.append(root_generator)    # push element on stack
        discovered[root_generator.get_name()+'_'+str(root_generator.get_id())] = root_generator
        while stack:
            generator = stack[-1]       # get element on the top of the stack
            del stack[-1]               # pop element on the top of the stack
            for bond in generator.get_outbonds():
                if bond.get_connector() and bond.get_type() == 'semantic':
                    # find generator closing the current out-bond
                    g_j = config.get_generator_by(bond.get_connector())
                    # check if has already been visited
                    if g_j.get_name()+'_'+str(g_j.get_id()) not in discovered:
                        stack.append(g_j)                                        # push element on stack
                        discovered[g_j.get_name()+'_'+str(g_j.get_id())] = g_j

        # dictionary whose keys are generator' names and values are pointers to those generators
        interacting_generators = {}
        for key in discovered:
            generator_name = key.split('_')[0]
            interacting_generators[generator_name] = discovered[key]
        del discovered

        return interacting_generators

    def __find_generator_representing_interacting_labels(self,interacting_generators):
        labels = self.__ontology.get_labels()
        matches = {}
        # find a label, i.e. a generator containing all names in interacting_generators
        for label in labels:
            if self.__ontology.get_level(label) != 4: continue
            # verify of each element in interacting generators is a substring of label
            match_count = 0
            found_label = True
            for name in interacting_generators:
                if label.find(name) < 0:
                    found_label = False
                    break
                match_count += 1
            # collect a match if one was found (a match here could be partial too: when the # of interacting labels is smaller)
            if found_label:
                matches[label] = match_count

        # find the match if there is one
        for label in matches:
            # assuming there is only one possible match, return it here
            if matches[label] == len(label.split('_')): #len(interacting_generators):
                del matches
                return label

        return None

    def __create_new_generator(self, label_name, cost, time):
        # collect all data to create a generator
        level = self.__ontology.get_level(label_name)
        modalities = self.__ontology.get_modalities(label_name)
        bond_structure = self.__ontology.get_bond_structure(label_name)

        # name,level,modality,type,cost,time
        new_generator = MyGenerator(label_name, level, modalities, 'ontological', cost, time)

        # set feature location associated to the new candidate
        #new_generator.set_rlocation(g_r.get_rlocation())

        # define the bond structure of the generator here
        new_generator.set_bond_structure(bond_structure)

        return new_generator

    # this proposal is limited to work with POSET topologies
    def propose_interaction_generator(self, config, from_level=3):
        ontological_generators = config.get_ontological_generators()
        if not ontological_generators: return config

        interaction_labels = []
        configuration_changed = False
        # look for a generator that involves interactions of the set of generators in s
        for generator in ontological_generators:
            # if the generator is from level 'from_level' and is not already connected to some interaction
            #print generator.get_name(),'generator level:',repr(generator.get_level()),' inbonds: ',repr(len(generator.get_inbonds()))
            if generator.get_level() == from_level: # and len(generator.get_inbonds()) < 1:
                # check already connected to higher level, if so, go to the next generator
                already_connected_to_higher_level = False
                inbonds = generator.get_inbonds()
                for bond in inbonds:
                    connector = bond.get_connector()
                    g = config.get_generator_by(connector)
                    if g.get_level() > from_level:
                        already_connected_to_higher_level = True
                        #print 'already connected to an interaction'
                        break

                if already_connected_to_higher_level: continue

                #print 'will connect to another one anyways'

                interacting_labels = self.__find_interactions(generator, config)
                #print 'interacting_labels: ',repr(interacting_labels)

                label = self.__find_generator_representing_interacting_labels(interacting_labels)
                #print 'label: ',label

                if label:
                    configuration_changed = True
                    #interaction_labels.append(label)
                    #print 'Interaction: ',label
                    any_generator = interacting_labels.values()[0]
                    # create a generator corresponding to the interaction
                    new_generator = self.__create_new_generator(label, cost=0, time=any_generator.get_time())
                    # add interaction generator to the configuration
                    config.add_generator(new_generator)
                    # close bonds
                    print repr(interacting_labels.values())
                    for g in interacting_labels.values():
                        # get score
                        score,status = self.compute_ontological_bond_weight(new_generator, g, config, False)
                        # compute energy
                        energy = self.compute_energy(score, self.__ont_w)
                        # close bonds
                        config.close_bonds(new_generator.get_id(), g.get_id(), energy)
        return config

#        if configuration_changed:
#            return config
#        else:
#            return None

        # add all possible interactions
        #for label_name in interaction_labels:

    # the idea is to propose a generator from higher levels in the hierarchy when there are available enough
    #


    # to propose generators that represent recipes -- for the other version, for generators representing interactions too
    def propose_super_generator(self,config,from_level=5):
        # find generators G' from level 4 in config
        ontological_generators = config.get_ontological_generators()
        if not ontological_generators: return config

        candidate_generators = []
        # look for a generator that involves interactions of the set of generators in s
        for generator in ontological_generators:
            # if the action generator is not already connected to some interaction
            if generator.get_level() == from_level and len(generator.get_inbonds()) < 1:
                candidate_generators.append(generator)

        # verify which generators from level 5 have out-bond values that allows bond interactions with generators in G'
        bond_structures = self.__ontology.get_bond_structures()
        for generator_name in bond_structures:
            for bond in bond_structures[generator_name]:
                bond_value = bond[0]


        # random select one of them'

    def __try_connect_ontological_generators(self, config, g_a, g_b):
        score,valid = self.compute_ontological_bond_weight(g_a, g_b, config)
        if not valid: score,valid = self.compute_ontological_bond_weight(g_b, g_a, config)
        if not valid: return False
        energy = self.compute_energy(score, self.__ont_w)
        return g_a.close_outbond(g_b, energy)

    def __find_compatible_bonds(self, g_i, g_j):
        bonds = []
        availability = []
        if g_i.is_inbond_of(g_j) == False and g_j.is_inbond_of(g_i) == False:
            for bond in g_i.get_outbonds():
                if bond.get_type() == 'semantic' and bond.get_value() in g_j.get_modality():
                    # keep track whether the bond is available or not
                    if bond.get_connector() == None: availability.append(1)
                    else: availability.append(0)
                    bonds.append(bond)

    def __find_generators_with_no_location_overlap(self, g, g_list):
        overlapping_generators = [ q for q in g_list if g.get_location().spatial_overlap(q.get_location()) > 0.0 == False ]
        return overlapping_generators


    def apply_spatial_coherence(self, config):
        ontological_generators = config.get_ontological_generators()
        if not ontological_generators: return config

        config.print_info()

        # first find a pair of generators that are connected but whose bounding boxes do not overlap
        offending_generator = None
        for g_k in ontological_generators:
            for bond in g_k.get_outbonds():
                if bond.get_connector() != None:
                    print 'connector id: ', bond.get_connector()
                    g_j = config.get_generator_by(bond.get_connector(), 'id')
                    if (g_k.get_location().spatial_overlap(g_j.get_location()) > 0.0) == False:
                        print 'the offending generator: '
                        offending_generator = g_j
                        offending_generator.print_info()
                        print 'with ',g_k.get_name(),g_k.get_id()
                        # break the connection
                        offending_generator.remove_inbond_by_id(bond.get_connector())
                        bond.remove_connector()
                        break
            if offending_generator: break

        if offending_generator == None: return config

        # disconnect all of its outbonds whose spatial overlap does not exist
        for bond in offending_generator.get_outbonds():
            if bond.get_connector() != None:
                g_j = config.get_generator_by(bond.get_connector(), 'id')
                if (offending_generator.get_location().spatial_overlap(g_j.get_location()) > 0.0) == False:
                    print 'disconnect outbond ', bond.get_value()
                    # break the connection
                    g_j.remove_inbond_by_id(bond.get_connector())
                    bond.remove_connector()

        # second step is attempting to connect to each other ontological generator with which it overlaps
        for g_k in ontological_generators:
            if offending_generator != g_k:
                if offending_generator.get_location().spatial_overlap(g_k.get_location()) > 0.0:
                    # try to connect one way
                    if self.__try_connect_ontological_generators(config, g_k, offending_generator) == False:
                        # try to connect the other way if the first way failed to connect
                        self.__try_connect_ontological_generators(config, offending_generator, g_k)

        print 'After correcting offender'
        config.print_info()

        return config

    def propose(self, config, with_temporal_bonds=False, selection_type='level', feature_thresh=0.5):
        ontological_generators = config.get_ontological_generators()
        if not ontological_generators: return config

        # First, select an ontological generator to be replaced in the configuration
        g_r = None
        level = 4
        while level == 4:
            g_r_index = self.sample('uniform', ontological_generators)
            g_r = ontological_generators[g_r_index]
            level = g_r.get_level()
        g_r_inbonds = g_r.get_inbonds()
        unconnected_feature_generators = []

        # Second, find the feature generators that explain such ontological generator
        cost = 0
        time = g_r.get_time()
        for inbond in g_r_inbonds:
            print 'inbond connector: ',inbond.get_value(),inbond.get_connector()
            if inbond.get_connector() != None:
                g = config.get_generator_by(inbond.get_connector(),'id')
                if g.get_type() == 'feature':
                    unconnected_feature_generators.append(g)

        print 'unconnected features: ',repr(unconnected_feature_generators)
        # print configuration information
        # config.print_info()

        # for when feature generator close their inbonds with outbonds of ontological generators
        if not unconnected_feature_generators:
            g_r_outbonds = g_r.get_outbonds()
            for outbond in g_r_outbonds:
                if outbond.get_connector() != None:
                    g = config.get_generator_by(outbond.get_connector())
                    if g.get_type() == 'feature':
                        unconnected_feature_generators.append(g)

        print 'REPLACE ',g_r.get_name()

        labels = None
        if selection_type == 'level':
            labels = self.__ontology.get_same_level_labels(g_r.get_name())
        else: # if by modality
            labels = self.__ontology.get_equivalent_labels(g_r.get_name())

#        print 'candidates for replacement: ',labels

        # select candidates uniformly random
        k = self.__k if self.__k <= len(labels) else max(self.__k,len(labels))
        candidates = random.sample(labels, k)

        candidate_configs = []
        candidate_generators = []
        for i in range(len(candidates)):
            # collect all data to create a generator
            label_name = candidates[i]
            level = self.__ontology.get_level(label_name)
            modalities = self.__ontology.get_modalities(label_name)
            bond_structure = self.__ontology.get_bond_structure(label_name)

            # name,level,modality,type,cost,time
            new_generator = MyGenerator(label_name, level, modalities, 'ontological', cost, time)

            # set feature location associated to the new candidate
            new_generator.set_rlocation(g_r.get_rlocation())

            # define the bond structure of the generator here
            new_generator.set_bond_structure(bond_structure)

            # create a new configuration in which the new candidate replaces the one to be remove
            #print 'removing generator ',g_r.get_id()
            new_config = config.replace(g_r, new_generator)

            # make changes to the connection of the new configuration given the newly added generator
            for feature_generator in unconnected_feature_generators:
                self.__place_support_bonds(feature_generator,new_generator,new_config,feature_thresh)
            self.__place_ontological_bonds(new_generator,new_config)

            # record newly proposed configs with
            candidate_configs.append(new_config)
            candidate_generators.append(new_generator)
            #self.__update_bonds_after_replacement(new_config,g_f,new_generator)

        if with_temporal_bonds:
            #print 'LOCAL PROPOSAL: TRYING TEMPORAL BONDS...'
            time.sort()

            # account for temporal bonds linking to the past
            for i in range(len(candidate_generators)):
                self.__place_past_ontological_bonds(candidate_generators[i],candidate_configs[i],time[0])

            # account for temporal connections linking to the future
            for i in range(len(candidate_generators)):
                self.__place_future_ontological_bonds(candidate_generators[i],candidate_configs[i],time[-1])

        # compute local energy contributions by new candidates configuration
        candidate_local_energies = []
        for i in range(len(candidate_generators)):
            # get local energy that is being contributed by new
            #candidate_configs[i].print_info()
            local_energy = candidate_configs[i].get_local_energy(candidate_generators[i],self.__bond_weights)
            #print 'i#', i, ' local energy: ', local_energy
            candidate_local_energies.append(local_energy)
#            os.system("read -p 'pause'")

        # select a candidate according to probability computed based on their locally contributed energy
        candidate_index = self.__probabilistic_candidate_selection(candidate_local_energies)

        # update the current configuration to the new one
        #self.__discard_configuration(config) # check if the upper code is making a copy of this configuration for other purposes
        new_proposal = candidate_configs[candidate_index]

        # discard temporary configurations, and others...
        del candidate_configs[candidate_index]
        for i in range(len(candidate_configs)):
            self.__discard_configuration(candidate_configs[0])

        del labels
        return new_proposal
