#!/usr/bin/python

import random
import math


class ProposalDistribution(object):

    def __init__(self):
        self.__ontology = None
        self.__predictor = None
    #		self.__predictor_label_map = {}

    def __init__(self, ontology, predictor):
        self.__ontology = ontology
        self.__predictor = predictor
    #		self.__predictor_label_map = {}

    #	def __init__(self,ontology,predictor,predictor_label_map):
    #		self.__ontology = ontology
    #		self.__predictor = predictor
    #		self.__predictor_label_map = predictor_label_map

    #	def add_predictor(self,predictor):
    #		if predictor not in self.__predictors:
    #			self.__predictors.append(predictor)

    # also works as an update function
    #	def add_predictor(self,predictor,label):
    #		if predictor not in self.__predictors:
    #			self.__predictors.append(predictor)
    #		self.__predictor_label_map[label] = predictor

    def sample(self, type, population):
        if type == 'uniform':
            return random.randrange(len(population))

    def compute_energy(self, score, k=1.):
        #return math.log(1.0001 - score, 2.0)
        energy = math.tanh(k * score)
        #print 'compute energy with score: ',score,' energy is ',energy
        return energy

    def propose(self, c):
        return c

    def thresh_function(self, score, thresh):
        # could be a probability distribution
        if score < thresh: return (-thresh + score)
        return score