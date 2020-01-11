import Configuration as config
import Generator as gen
import SupportBond as sup_b
import SemanticBond as sem_b
import TemporalBond as tem_b
from itertools import count
from copy import deepcopy
import random
import Inference as inf
import time
import os
import operator

semBondWeight = 0.5
supBondWeight = 2.5 

def PatternTheory(inputFile, semanticBondPath, topK, outFile):
	BondID = count(0)
	genID = count(0)
	localSwapSpace = {}
	topKLabel = 0
	priorScale = 100

	#Load Feature labels and create feature generators
	equivalence = {}
	feature_generators = []
	with open(inputFile) as f:
		for featFile in f:
			feat = str.split(featFile.replace('\n', ''))
			feat = str.split(featFile.replace('/home/saakur/Desktop/', './'))
			equivalence = {}
			with open(feat[1]) as fl:
				for line in fl:
					l = str.split(line.replace('\n', ''))
					equivalence[l[0]] = float(l[1])
			if topKLabel > 0:
				sorted_equiv = sorted(equivalence.items(), key=operator.itemgetter(1), reverse=True)
				equivalence = {}
				for k,v in sorted_equiv[:topKLabel]:
					equivalence[k] = v*supBondWeight

			G = gen.Generator(next(genID), feat[0], feat[0], "Feature", feat[0])
			supBG = sup_b.SupportBond(next(BondID), "SupportBond", "OUT", G.generatorID)
			supBG.compatible = deepcopy(equivalence)
			G.addOutBond(supBG)
			feature_generators.append(G)
			localSwapSpace[G.feature] = []

	filelist = [ f for f in os.listdir(semanticBondPath) if f.endswith(".txt")]

	semBondDict = {}

	#Load semantic bonds 
	for semanticBondFile in filelist:
		semBondName = str.split(str.split(semanticBondFile.replace('\n', ''), '_').pop(), '.')[0]
		if semBondName not in semBondDict.keys():
			semBondDict[semBondName] = {}

		equivalence = {}
		with open(semanticBondPath+semanticBondFile) as fl:
			for line in fl:
				semBondDict_Concept = {}
				l = str.split(line.replace('\n', ''), ',')
				label = l.pop(0)
				label = str.split(label,'-')[0]

				for l1 in l:
					l2 = str.split(l1.replace('\n', ''), ':')

					if(semBondName != "Similarity"):
						semBondDict_Concept[l2[0]] = float(l2[1]) * priorScale * semBondWeight
					else:
						semBondDict_Concept[l2[0]] = float(l2[1]) * semBondWeight * priorScale
				equivalence[label] = dict(semBondDict_Concept.copy())
		semBondDict[semBondName] = dict((equivalence.copy()))

	#For each of the feature generators, create generators for each of the label possibilties
	# and bonds for each of the generators
	for g in feature_generators:
		#Determine the label category to create generators for them
		genType = g.generatorName
		
		#For each of the outbound bonds of the feature generators, create the generators for each of the label candidates
		for bondID in g.outBonds.keys():
			b = g.outBonds[bondID]
			#For each of the each of the label candidates, create the generators and bonds 
			for label in b.compatible:
				#Create the generator
				G = gen.Generator(next(genID), label, label, genType, g.generatorName)
				#Create and add complementary support bond
				supBG_IN = sup_b.SupportBond(next(BondID), "SupportBond", "IN", G.generatorID)
				G.addInBond(supBG_IN)
				for semBondName in semBondDict.keys():
					if label in semBondDict[semBondName].keys():
						#Create a semantic bond
						semBG_OUT = sem_b.SemanticBond(next(BondID), semBondName, "OUT", G.generatorID)
						#Add the equivalence table for the semantic bond
						semBG_OUT.compatible = deepcopy(semBondDict[semBondName][label])
						#Create complementary semantic bond
						semBG_IN = sem_b.SemanticBond(next(BondID), semBondName, "IN", G.generatorID)
						#Add created bonds to the generator
						G.addOutBond(semBG_OUT)
						G.addInBond(semBG_IN)
				
				#Add created generator to list with generators of equivalent modality
				localSwapSpace[G.feature].append(G)

	globalSwapSpace = {}
	for fg in feature_generators:
		globalSwapSpace[fg.generatorID] = fg

	debugFIle = "./debugFile.txt"
	# globalProposalChance Helps avoid local minima. Need to be less than 1 when using MCMC candidate proposal
	globalProposalChance = 1.0
	PS = inf.Inference(localSwapSpace, globalSwapSpace, False, debugFIle, topK, globalProposalChance)
	topKConfig = PS.run_inference()

	topVal = 1
	ftFile = open(outFile, 'w')
	ftFile.write("Top %s results:\n" %topK)
	ftFile.close()
	for key in sorted(topKConfig):
		topKConfig[key].printConfig(outFile, localSwapSpace.keys())
		topVal += 1

	# Clean up for Anneal
	filelist = [ f for f in os.listdir(".") if f.endswith(".state") ]
	for f in filelist:
		os.remove(f)

def main():

	inputPath = "./S1_PreProcessFiles/"

	outputPath = "./BA_S1_Out/"

	if not os.path.exists(outputPath):
		os.makedirs(outputPath)

	filelist = [ f for f in os.listdir(inputPath)]

	semanticBondPath = "./HRC_Priors/OnlyHC_IsA/"

	topK = 10

	start_time = time.time()

	for file in filelist:
		inputFile = inputPath + file
		if os.path.isdir(inputFile):
			print "Folder!!!"
			continue
		# if "features_P03_cereals_cam01" not in file:
		# 	continue
		print file
		data = str.split(file.replace('\n', ''), "_")

		outputFile = outputPath + "_".join(i for i in data) + "_" + str(topK) + "_results.txt"
		outputFile = outputPath + "_".join(i for i in data) + "_" + str(topK) + "_results.txt"

		PatternTheory(inputFile, semanticBondPath, topK, outputFile)
		break

	print("--- %s seconds ---" % (time.time() - start_time))

if __name__ == '__main__':
	main()