from __future__ import print_function
import math
import random
from anneal import Annealer
import numpy as np
import Configuration as conf
from random import randrange
import copy

random.seed(12345)

class MCMC_Inference(Annealer):

	def __init__(self, state, initConfig, global_proposal, localSwapSpace, globalSwapSpace, topK, debugFlag, debugFile):
		#Define class for optimization. 
		self.global_proposal = global_proposal #Global proposal probability
		self.localSwapSpace = localSwapSpace #Local Swap Space. Dict with keys being support feature name and respective label generators
		self.globalSwapSpace = globalSwapSpace #Local Swap Space. List of feature support generators
		self.currConfig = initConfig #Initial configuration
		self.topK_Config = {} #Contains list of top "K" Configurations
		self.topK = topK
		self.debug = debugFlag #Debug flag
		self.debugFile = debugFile #Debug File Name
		super(MCMC_Inference, self).__init__(state)  # important! 

	#Local proposal function
	def localProposal(self):
		gCount = self.currConfig.get_gCount()
		chance = random.uniform(0, 1)

		if gCount < 1:
			self.globalProposal()

		else:
			# currGenSpace = set(self.currConfig.generators.keys()) - set(self.globalSwapSpace.keys())
			l1 = self.currConfig.generators.keys()
			l2 = self.globalSwapSpace.keys()
			currGenSpace = [x for x in l1 if x not in l2]

			randomPopGen  = self.currConfig.generators[self.currConfig.getHighestGen(currGenSpace)]
			self.currConfig.removeGenerator(randomPopGen.generatorID)


			fl = randomPopGen.feature
			currGenSpace = self.localSwapSpace[fl]
			random_index = randrange(0,len(currGenSpace))
			self.currConfig.addGenerator(currGenSpace[random_index])

			if self.checkDuplicate():
				chance = random.uniform(0, 1)
				if chance < self.global_proposal:
					self.localProposal()
				else:
					self.globalProposal()
			if gCount < 1:
				self.globalProposal()
			
	#Global Proposal Function
	def globalProposal(self):
		# print("global proposal!!", self.global_proposal)
		currConfigGen = self.currConfig.generators.keys()
		self.currConfig.resetConf()
		#Add feature generators
		featureLabel = []
		for g in self.globalSwapSpace.values():
			self.currConfig.addGenerator(g)
			featureLabel.append(g.label)

		#Add random label generators
		for fl in featureLabel:
			currGenSpace = self.localSwapSpace[fl]
			# print(type(currGenSpace))
			random_index = randrange(0,len(currGenSpace))
			genID = self.localSwapSpace[fl][random_index].generatorID
			while genID in currConfigGen:
				# print(genID, currConfigGen)
				random_index = randrange(0,len(currGenSpace))
				genID = self.localSwapSpace[fl][random_index].generatorID
			self.currConfig.addGenerator(self.localSwapSpace[fl][random_index])


	def move(self):
		#Local and Global Proposals
		p = np.random.uniform(0.0, 1.0)
		
		if p < self.global_proposal:
			self.localProposal()
		
		else:
			self.globalProposal()

	def energy(self):
		currEnergy = self.currConfig.getEnergy()
		topKEnergy = self.topK_Config.keys()
		if not topKEnergy:
			self.topK_Config[currEnergy] = copy.deepcopy(self.currConfig)
			return currEnergy
		else:
			maxVal = max(topKEnergy)
		if maxVal > currEnergy:
			if len(topKEnergy) > self.topK:
				del self.topK_Config[maxVal]
			self.topK_Config[currEnergy] = copy.deepcopy(self.currConfig)

		if self.debug:
			self.currConfig.printConfig(self.debugFile, self.globalSwapSpace.keys())
		return currEnergy

	def checkDuplicate(self):
		s1 = self.currConfig.getGeneratorSet()
		confSets = []
		for c in self.topK_Config.values():
			confSets.append(c.getGeneratorSet())
		if not confSets:
			return False
		for s2 in confSets:
			if not list(s1 - s2):
				return True

	def checkDuplicate_V2(self):
		s1 = self.currConfig.getGeneratorSet()
		confSets = []
		
		for c in self.topK_Config.values():
			confSets.append(c.getGeneratorSet())
		
		isDuplicate = False;

		if confSets:
			for s2 in confSets:
				# if not list(s1 - s2):
				if s1 == s2:
					isDuplicate = True
					break
		return isDuplicate


	def getTopK(self):
		return self.topK_Config

class Inference:
	def __init__(self, localSwapSpace, globalSwapSpace, debugFlag, debugFile, topK = 10, global_proposal = 1.0):
		self.global_proposal = global_proposal #Global proposal probability
		self.localSwapSpace = localSwapSpace #Local Swap Space. Dict with keys being support feature name and respective label generators
		self.globalSwapSpace = globalSwapSpace #Local Swap Space. Dict with keys being support feature name and generators
		self.initConf = conf.Configuration(0, "Init")
		self.init_state = list(range(0,10))
		self.topK = topK
		self.debug = debugFlag #Debug flag
		self.debugFile = debugFile #Debug File Name

		self.PT_Inf = MCMC_Inference(self.init_state, self.initConf, self.global_proposal, self.localSwapSpace, self.globalSwapSpace, self.topK, self.debug, self.debugFile)
		self.PT_Inf.Tmax = 25000.0  # Max (starting) temperature
		self.PT_Inf.Tmin = 2.5      # Min (ending) temperature
		self.PT_Inf.steps = 10000   # Number of iterations
		self.PT_Inf.updates = 100   # Number of updates (by default an update prints to stdout)
		# since our state is just a list, slice is the fastest way to copy
		self.PT_Inf.copy_strategy = "slice"  

	def run_inference(self):
		state, e = self.PT_Inf.anneal()
		print(e)
		print(state)
		return self.PT_Inf.topK_Config