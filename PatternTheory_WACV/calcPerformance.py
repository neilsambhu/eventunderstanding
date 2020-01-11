from __future__ import division
import numpy as np
import os
inputPath = "./BA_S1_Out/"

filelist = [ f for f in os.listdir(inputPath)]
value = []
values = {}
fullCorrect = 0
numCorrect = 0
actions = ["cut","walk_in","spoon","peel","stir","walk_out", "smear","put","squeeze", "butter", "pour", "fry", "crack", "take", "add"]
objects = ["topping", "topping_on_top", "coffee", "teabag", "plate", "eggs", "juice", "salt_and_pepper", "milk", "powder", "bun_together", "fruit", "tea", "pancake", "cereals", "sugar", "bun", "bowl", "egg", "glass", "water", "orange", "pan", "cup", "oil", "dough", "flour", "squeezer", "butter", "knife"]
limitedVocab = [["stir", "tea"], ["take", "butter"], ["take", "eggs"], ["pour", "flour"], ["pour", "sugar"], ["stir", "fruit"], ["take", "squeezer"], ["take", "topping"], ["stir", "coffee"], ["spoon", "sugar"], ["stir", "cereals"], ["pour", "egg", "pan"], ["put", "bunTogether"], ["take", "knife"], ["stir", "egg"]]
totA = 0
totB = 0
print "Num indpendent videos:", len(filelist)
for topK in range(10):
	acList = []
	objList = []
	totalA = 0
	totalO = 0
	value = []
	values = {}
	fullCorrect = 0
	numCorrect = 0
	for inputFile in filelist:
		truthValue = []
		data = str.split(inputFile.replace('\n', ''), "_")
		dataVal = []
		dataVal.append(data[0])
		dataVal.append(data[1])
		dataVal.append(data[2])
		dataVal.append(data[3])
		dataVal.append(data[4])
		videoName = "_".join(i for i in dataVal)
		truthValue.append(data[3])
		truthValue.append(data[4])

		if data[3] or data[4] in actions:
			totalA += 1
		if data[3] or data[4] in objects:
			totalO += 1

		with open(inputPath+inputFile) as f:
			lineCount = 0
			percentOverlap = []
			aList = []
			oList = []
			for line in f:
				a=0
				o=0
				if lineCount <= topK:# and lineCount < 3:
					if line.isspace() or line == "\r":
						# print inputFile, line
						continue
					genVal = []
					val = str.split(line.replace('\n', ''), "_")
					if len(val) <= 1:
						continue
					genVal.append(str.split(val[0], '-')[0])
					genVal.append(str.split(val[1], '-')[0])
					p = float(len(set(truthValue) & set(genVal)) / (len(truthValue)))
					for d1 in genVal:
						if d1 in truthValue:
							if d1 in actions:
								a += 1
							elif d1 in objects:
								o += 1
					percentOverlap.append(len(set(truthValue) & set(genVal)) / (len(truthValue)))
					aList.append(a)
					oList.append(o)
				lineCount += 1
			# print percentOverlap
			value.append(max(percentOverlap))
			acList.append(max(aList))
			objList.append(max(oList))
			if videoName in values:
				values[videoName].append(max(percentOverlap))
			else:
				values[videoName] = []
				values[videoName].append(max(percentOverlap))
	if topK <= 1:
		totA = totalA
		totO = totalO

	avgVal = values.values()
	val = []
	percentNone = 0
	for i in avgVal:
		val.append(np.mean(i))
		fullCorrect += i.count(1)
		numCorrect += sum(j > 0 for j in i)
		if sum(j > 0 for j in i) == 0:
			percentNone += 1

# print values
print "Num composite videos:", len(values.keys())
print "Average Performamce :%s" % np.mean(val)
print "Zero match Composite Videos:", percentNone 
print fullCorrect
print "Correct Actions", sum(acList)/totA
print "Corret Objects", sum(objList)/totO
