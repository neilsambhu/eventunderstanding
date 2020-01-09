#!/usr/bin/python

from Ontology import *
from Configuration import *
from ProposalDistribution import *

import math

class GlobalProposal(ProposalDistribution):

    def __init__(self,ont,pred,strict_mode=True,time_unit=1):
        super(GlobalProposal,self).__init__(ont, pred)
        self.__ont_w = 0.001
        self.__ontology = ont
        self.__predictor = pred
        self.__strict_mode = strict_mode
        self.__time_unit = time_unit
        #self.__feature_thresh = feature_support_thresh

    def set_time_unit(self,time_unit):
        self.__time_unit = time_unit

    def get_time_unit(self):
        return self.__time_unit

    def __find_best_score_label_index(self, top_labels):
        label_index = 0
        score = top_labels[label_index].score
        for i in range(1,len(top_labels)):
            if score < top_labels[i].score:
                label_index = i
                score = top_labels[i].score
        return label_index

    def __mean(self, values):
        m_i = 0.0
        n = 0
        for key in values:
            m_i += values[key]
            n += 1.0
        return m_i / n

    def __get_interaction_name(self,g_k,config):
        label = g_k.get_name()
        if g_k.get_level() == 'level3':
            connected_objects = []
            for outbond in g_k.get_outbonds():
                if outbond.get_connector() != None:
                    g_t = config.get_generator_by(outbond.get_connector())
                    if g_t.get_level() == g_k.get_level()-1:
                        connected_objects.append(g_t.get_name())
            label += '_' + connected_objects[random.sample(len(connected_objects),1)[0]]
            del connected_objects
        elif g_k.get_level() == 'level2':
            for inbond in g_k.get_inbonds():
                # if an inbond exists, then there is a connector (the same is not true for outbonds)
                g_t = config.get_generator_by(inbond.get_connector())
                if 'actions' in g_t.get_modality():
                    label = g_t.get_name() + '_' + label
                    break
        return label

    def compute_ontological_bond_weight(self,g_i,g_j,config,time_based_bond=False):
        label_i = g_i.get_name()
        label_j = g_j.get_name()

        n_ij = 0.0
        validity = False
        if time_based_bond:
            n_ij,validity = self.__ontology.time_based_prior(label_i,label_j)
        else:
            n_ij,validity = self.__ontology.prior(label_i,label_j)

        #print 'n_ij',n_ij,'validity',validity

        return -n_ij,validity

    def __intersect(self,list_a,list_b):
        return list(set(list_a) & set(list_b))

    def propose(self, jump_config, feature_thresh, with_temporal_bonds=False, type='random'):
        #		print 'BEFORE GLOBAL PROPOSAL:'
        #	c.print_info()

        h = Configuration()
        h.set_current_time(jump_config.get_current_time())

        ontological_generators = jump_config.get_ontological_generators()
        feature_generators = jump_config.get_feature_generators()
        free = range(len(feature_generators))

        # print 'closing grounding bonds...'
        while len(free) > 0:
            # select a feature generator to be explained
            index = self.sample('uniform', free)
            g_f = feature_generators[free[index]].get_copy()

            # add it to the new configuration
            h.add_generator(g_f)

            # get the top explanations for this feature generator
            top_labels= g_f.get_top_labels()

            # select one of the top labels to explain the feature generator
            label_index = None
            if type == 'best':
                label_index = self.__find_best_score_label_index(top_labels)
            else:
                #print g_f.get_features() + ' top labels: ' + repr(top_labels)
                label_index = self.sample('uniform', top_labels)

            # energy of support bond
            score = self.thresh_function(top_labels[label_index].score,feature_thresh)
            energy = self.compute_energy(-score, 2.0)
            new_generator = jump_config.get_generator_by(top_labels[label_index].g_id).get_copy()
#            print 'new generators time: ' + repr(new_generator.get_time())
            h.add_generator(new_generator)

            #			print top_labels[label_index].name + ' bond score: ' + repr(top_labels[label_index].score)
            if h.close_bonds(g_f.get_id(), top_labels[label_index].g_id, energy, False, self.__strict_mode) == False:
                h.close_bonds(top_labels[label_index].g_id, g_f.get_id(), energy, False, self.__strict_mode)
            else:
                if (g_f.get_name() == 'hof' and top_labels[label_index].name == 'butter-o') or (g_f.get_name() == 'hog' and top_labels[label_index].name == 'butter-a'):
                    print 'bonding g_f(', g_f.get_name(), ') and g_o(', top_labels[label_index].name, '), weight = ', \
                        score, ', energy = ', energy
                    exit(1)

            #	pass
            #	print 'bond closed successfully'
            del free[index]

        generators = h.get_ontological_generators()
        for i in range(len(generators)):
            for j in range(i+1, len(generators)):
                # temporal connections could be treated here or in the ontology
                if self.__intersect(generators[i].get_time(), generators[j].get_time()):
                    #if ontology.obeys_constraints(g_i.get_name(),g_j.get_name())
                    #score = self.__ontology.prior(g_i.get_name(),g_j.get_name())
                    score,valid = self.compute_ontological_bond_weight(generators[i], generators[j],h)
 #                   print 'score: ',score,' valid: ',valid
                    if not valid:
                        score,valid = self.compute_ontological_bond_weight(generators[j], generators[i],h)
                    energy = self.compute_energy(score, self.__ont_w)
                    if h.close_bonds(generators[i].get_id(), generators[j].get_id(), energy, False, self.__strict_mode) == False:
                        h.close_bonds(generators[j].get_id(), generators[i].get_id(), energy, False, self.__strict_mode)

        if with_temporal_bonds:
#            print 'ADD TEMPORAL BONDS IF POSSIBLE'
            # account for temporal bonds linking to the past
            for i in range(len(generators)):
                time = generators[i].get_time()
#                print 'times: ' + repr(generators[i].get_time())
                current_time = time[0]
                self.__place_past_ontological_bonds(generators[i],h,current_time)

            # account for temporal connections linking to the future
            for i in range(len(generators)):
                time = generators[i].get_time()
                current_time = time[-1]
                self.__place_future_ontological_bonds(generators[i],h,current_time)

            #		h.print_info()
        return h

    # assume that g_k is being treated for time 'current_time'
    def __place_ontological_bonds(self,g_k,config):
        time_based_bond = False
        # close bonds between ontological generators
        ontological_generators = config.get_ontological_generators()
        for g_j in ontological_generators:
            if g_k.get_id() != g_j.get_id():
                # temporal connections could be treated in a higher level layer where those are weighed or here
                # if g_k.get_time() == g_j.get_time():
                if self.__intesect(g_k.get_time(),g_j.get_time()):
                    # if ontology.obeys_constraints(g_b.get_name() ,g_j.get_name())
                    #score = self.__ontology.gprior(g_k,g_j)
                    score,valid = self.compute_ontological_bond_weight(g_k,g_j,config,time_based_bond)
                    if not valid:
                        score,valid = self.compute_ontological_bond_weight(g_j,g_k,config,time_based_bond)
                    energy = self.compute_energy(score, self.__ont_w)
                    # try connections in both directions, whichever works
                    if config.close_bonds(g_k.get_id(),g_j.get_id(),energy,time_based_bond,self.__strict_mode) == False:
                        config.close_bonds(g_j.get_id(),g_k.get_id(),energy,time_based_bond,self.__strict_mode)

    def __place_past_ontological_bonds(self,g_k,config,current_time):
        time_based_bond = True
        ontological_generators = config.get_ontological_generators()
        for g_j in ontological_generators:
            if g_k.get_id() != g_j.get_id():
                if self.__intersect(g_j.get_time(), [current_time - self.__time_unit]):
                    #score = self.__ontology.gtime_based_prior(g_j,g_k)
                    score,valid = self.compute_ontological_bond_weight(g_j,g_k,config,time_based_bond)
                    if valid:
                        energy = self.compute_energy(score, self.__ont_w)
                        config.close_bonds(g_j.get_id(),g_k.get_id(),energy,time_based_bond,self.__strict_mode)

    def __place_future_ontological_bonds(self,g_k,config,current_time):
        time_based_bond = True
        ontological_generators = config.get_ontological_generators()
        # future connections
        for g_j in ontological_generators:
            if g_k.get_id() != g_j.get_id():
                if self.__intersect(g_j.get_time(),[current_time + self.__time_unit]):
                    #score = self.__ontology.gtime_based_prior(g_k,g_j)
                    score,valid = self.compute_ontological_bond_weight(g_k,g_j,config,time_based_bond)
                    if valid:
                        energy = self.compute_energy(score, self.__ont_w)
                        config.close_bonds(g_k.get_id(),g_j.get_id(),energy,time_based_bond,self.__strict_mode)

    def __place_support_bonds(self, g_f, g_o, config, feature_thresh):
        time_based_bond = False
        score = self.__predictor.run(g_o.get_name(),g_f)
        score = self.thresh_function(score,feature_thresh)               # to let positive values to
        energy = self.compute_energy(-score, 2.0)
        if config.close_bonds(g_f.get_id(),g_o.get_id(),energy,time_based_bond,self.__strict_mode) == False:
            config.close_bonds(g_o.get_id(),g_f.get_id(),energy,time_based_bond,self.__strict_mode)
        else:
            if (g_f.get_name() == 'hof' and g_o.get_name() == 'butter-o') or (g_f.get_name() == 'hog' and g_o.get_name() == 'butter-a'):
                print 'bonding g_f(', g_f.get_name(), ') and g_o(', g_o.get_name(), '), weight = ', \
                        score, ', energy = ', energy
                exit(1)
