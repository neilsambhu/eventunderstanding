import SupportBond as sup_b
import SemanticBond as sem_b
import TemporalBond as tem_b
import Generator as gen
import copy 

class Configuration:
	# Define a new instance of a configuration
	def __init__(self, configID, configName):
		self.generators = {} #List of generators in the configuration
		self.configID = configID #Configuration ID
		self.configName = configName #Configuration Name
		self.energy = 0 # Overall configuration energy

	# Add a new generator to the configuration
	def addGenerator(self, generator):
		# print "-----------Add Gen %s ----------------"%generator.generatorName
		for g in self.generators.values():
			# print g.generatorID, g.generatorName
			bonds = g.inBonds.values() + g.outBonds.values()
			for b in bonds:
				if b.status:
					continue
				candBonds = generator.inBonds.values() + generator.outBonds.values()
				for candBond in candBonds:
					if not candBond.status:
						success, updtBond = g.addBondConnection(b.ID, candBond, generator.label, generator.generatorID)
						if success:
							generator.updateBond(updtBond)
		self.generators[generator.generatorID] = generator
		self.updateConfig()
		# print "-----------Status after Add Gen %s ----------------"%generator.generatorName
		# self.configStatus()

	# Get number of generators in configuration
	def get_gCount(self):
		return len(self.generators.keys())

	# Update configuration status
	def updateConfig(self):
		for g in self.generators.values():
			g.updateStatus()
		self.getEnergy()

	# Get total energy of configuration:
	def getEnergy(self):
		self.energy = 0
		for g,v in self.generators.items():
			self.energy += v.energy
		return self.energy

	def resetConf(self):
		# self.generators.clear()
		# self.energy = 0
		for g in self.generators.keys():
			self.removeGenerator(g)
		self.updateConfig()


	def configStatus(self):
		self.updateConfig()
		print "Energy = %s"%self.energy
		for g in self.generators.values():
			print g.generatorID, g.label, g.Active, g.arity, g.energy

	def getGeneratorSet(self):
		return set(self.generators.keys())

	def removeGenerator(self, generator):
		strayBonds = self.generators[generator].resetGenerator()
		for (bondID, genID) in strayBonds:
			if bondID is None and genID is None:
				pass
			else:
				isValid, bond, direction = self.generators[genID].getBond(bondID)
				if bond is not None and bond.status:
					if direction:
						self.generators[genID].removeOutBond(bond)
					else:
						self.generators[genID].removeInBond(bond)
		del self.generators[generator]
		self.updateConfig()

	def checkRegularity(self):
		for g in self.generators.values():
			for b in g.inBonds.values() + g.outBonds.values():
				if b.type != "Support":
					pass
				else:
					if not b.status:
						self.removeGenerator(g.generatorID)

	def getHighestGen(self, genList):
		self.updateConfig()
		energyDict = {}
		for genID in genList:
			energyDict[self.generators[genID].swapEnergy()] = genID
		return energyDict[max(energyDict.keys())]

	def getHighestGen_V1(self, genList):
		self.updateConfig()
		energyDict = {}
		for genID in genList:
			energyDict[self.generators[genID].energy] = genID
		return energyDict[max(energyDict.keys())]

	def printConfig(self, fileName, noPrintKeys):
		printKeys = []
		for g in self.generators.values():
			if g.label not in noPrintKeys:
				printKeys.append(g.label)
		ftFile = open(fileName, 'a')
		ftFile.write("_".join(i for i in printKeys))
		ftFile.write("\n")
		ftFile.close()


	def printFeat_Grounded_Config(self, fileName, noPrintKeys):
		printKeys = []
		for g in self.generators.values():
			if g.label in noPrintKeys:
				bonds = g.inBonds.values() + g.outBonds.values()
				for b in bonds:
					if b.type == "Support" and b.status:
						printKeys.append(','.join([g.label, self.generators[b.compGenID].label]))
				# printKeys.append(g.label)
		ftFile = open(fileName, 'a')
		for i in printKeys:
			ftFile.write(i + "\n")
		# ftFile.write("------\n")
		ftFile.close()

	def debugConfig(self, fileName):
		ftFile = open(fileName, 'a')
		ftFile.write("\n--------------------------------------------------\n")
		ftFile.write("\n--------------------------------------------------\n")
		ftFile.write("\n--------------------------------------------------\n")
		for g in self.generators.values():
			ftFile.write("g.label: " + str(g.label))
			ftFile.write("\t")
			ftFile.write("g.arity: " + str(g.arity))
			ftFile.write("\t")
			ftFile.write("g.Active: " + str(g.Active))
			ftFile.write("\t")
			ftFile.write("g.energy: " + str(g.energy))
			ftFile.write("Bonds:\n")
			bonds = g.inBonds.values() + g.outBonds.values()
			for b in bonds:
				ftFile.write("\n")
				ftFile.write("b.name: " + str(b.name))
				ftFile.write("\n")
				ftFile.write("b.ID: " + str(b.ID))
				ftFile.write("\n")
				ftFile.write("b.type: " + str(b.type))
				ftFile.write("\n")
				ftFile.write("b.compatible: " + str(b.compatible))
				ftFile.write("\n")
				ftFile.write("b.energy: " + str(b.energy))
				ftFile.write("\n")
				ftFile.write("b.status: " + str(b.status))
				ftFile.write("\n")
				ftFile.write("b.currGen: " + str(b.currGen))
				ftFile.write("\n")
				ftFile.write("b.direction: " + str(b.direction))
				ftFile.write("\n")
				ftFile.write("b.compBondID: " + str(b.compBondID))
				ftFile.write("\n")
				ftFile.write("b.compGenID: " + str(b.compGenID))
				ftFile.write("\n")
			ftFile.write("\n--------------------------------------------------\n")
		ftFile.close()
