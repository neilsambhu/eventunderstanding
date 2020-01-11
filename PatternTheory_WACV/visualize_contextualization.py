from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os, requests, json, sys
import numpy as np
import cPickle as pickle
import time
import datetime

def getEquivalence(item):
	equivalent = {}
	query = 'http://api.conceptnet.io/query?start=/c/en/' + item + '&language=/c/en?format=json'
	try:
		obj = requests.get(query).json()
	except Exception as e:
		print("Query",query)
		print("Error:", e)
		try:
			r = requests.get(query)
			obj = json.loads(r.text)
		except Exception as e1:
			print("Query1",query)
			print("Error1:", e)

	if not obj:
		print (item, query)
		return equivalent
	if len(obj['edges']) > 0:
		for i in obj['edges']:
			relation = i['rel']['label']
			weight = i['weight']
			label = i['end']['label']
			try:
				if i['end']['language'] not in ['en']:
					continue
			except:
				continue
			labelID = i['end']['@id']
			equivalent[labelID] = weight
	return equivalent

def getPrior(item, other):
	priors = []
	concepts = []

	url = 'http://api.conceptnet.io/query?node=/c/en/' + item + '&other=' + '/c/en/' + other
	# print url
	obj = requests.get(url).json()
	if not obj:
		return 0

	if len(obj['edges']) > 0:
		for i in obj['edges']:
			return i['weight']
			
	return 0

def getDirectDict(combos):
	DirectDict = {}
	totMiniBatch = len(combos)
	num_minibatch = 0
	for combo in combos:
		num_minibatch += 1
		item1, item2 = combo
		print('\rGetting Direct Prior. Completed [%f%%]'%(num_minibatch/(totMiniBatch*1.0)), end="")
		sys.stdout.flush()
		if combo not  in DirectDict:
			wt = getPrior(item1, item2)
			if wt > 0:
				DirectDict[str(combo)] = wt
		
	with open("DirectDict.json", "w") as of:
		json.dump(DirectDict, of, indent=4, sort_keys=True)

	return DirectDict

def getL1Dict(combos):
	L1Dict = {}

	totMiniBatch = len(combos)
	num_minibatch = 0

	for combo in combos:
		num_minibatch += 1
		print('\rGetting L1 Prior. Completed [%f%%]'%(num_minibatch/(totMiniBatch*1.0)), end="")

		item1, item2 = combo
		
		# if item1 in L1Dict and item2 in L1Dict:
		# 	continue	

		if item1 not in L1Dict:
			L1Dict[item1] = []

		if item2 not in L1Dict:
			L1Dict[item2] = []

		if L1Dict[item1]:
			continue
		e = getEquivalence(item1)

		for c,wt in e.iteritems():
			c = c.split('/')[3]
			L1Dict[item1].append([item1, c, wt])
		
		if L1Dict[item2]:
			continue
		e = getEquivalence(item2)

		for c,wt in e.iteritems():
			c = c.split('/')[3]
			L1Dict[item2].append([item2, c, wt])

	with open("./L1Dict.json", "w") as of:
		json.dump(L1Dict, of, indent=4, sort_keys=True)

	return L1Dict

def getL2Dict(combos, outFile):
	L2Dict = {}

	totMiniBatch = len(combos)
	num_minibatch = 0

	for combo in combos:

		num_minibatch += 1
		print('\rGetting L2 Prior. Completed [%f%%]'%(num_minibatch/(totMiniBatch*1.0)), end="")
		# print (combo)
			
		item1, item2, wt1 = combo

		if item1 not in L2Dict:
			L2Dict[item1] = []

		# if L2Dict[item1]:
		# 	continue

		e = getEquivalence(item2)

		for c,wt in e.iteritems():
			c = c.split('/')[3]
			L2Dict[item1].append([item1, item2, c, wt])

		# break

	with open(outFile, "w") as of:
		json.dump(L2Dict, of, indent=4, sort_keys=True)

	return L2Dict


def getL3Dict(combos, outFile):
	L3Dict = {}

	totMiniBatch = len(combos)
	num_minibatch = 0
	print (totMiniBatch)
	pt = 0
	for combo in combos:

		num_minibatch += 1

		if num_minibatch % 5000 == 0:
			pt += 1
			print('Sleeping for 1 hr to avoid interruption... Time now: %s'%(str(datetime.datetime.now())))
			with open(outFile+'.pt'+str(pt), "w") as of:
				json.dump(L3Dict, of, indent=4, sort_keys=True)
			time.sleep(60*30)

		print('\rGetting L3 Prior. Completed [%f%%]'%(num_minibatch/(totMiniBatch*1.0)), end="")
		# print (combo)
			
		item1, c1, c2, wt1 = combo

		if item1 not in L3Dict:
			L3Dict[item1] = []

		# if L3Dict[item1]:
		# 	continue
		try:
			e = getEquivalence(c2)
		except:
			print(num_minibatch, '\t', item1, c1, c2)
			with open('ErrorLog.txt', 'a') as f:
				f.write('Failed:%s\t%s\t%s\n'%(str(item1),str(c1),str(c2)))

			continue

		for c,wt in e.iteritems():
			c = c.split('/')[3]
			L3Dict[item1].append([item1, c1, c2, c, wt])

		# break

	with open(outFile, "w") as of:
		json.dump(L3Dict, of, indent=4, sort_keys=True)

	return L3Dict

def constructCues(combos, L1Dict, L2Dict, L3Dict, outFile):
	totMiniBatch = len(combos)
	num_minibatch = 0

	edgeList = {}

	for combo in combos:
		print('\rConstructing Cues. Completed [%f%%]'%(num_minibatch/(totMiniBatch*1.0)), end="")
		item1, item2 = combo
		if str(combo) in DirectDict:
			edgeList[str(combo)] = [item1, item2, DirectDict[str(combo)]]
			continue
		if item1 == 'None' or item2 == 'None':
			edgeList[str(combo)] = [item1, item2, '0']
			continue

		item1L1 = L1Dict[item1]
		item1L2 = L2Dict[item1]
		item1L3 = L3Dict[item1]

		item2L1 = L1Dict[item2]
		item2L2 = L2Dict[item2]
		item2L3 = L3Dict[item2]

		eList = []

		# if combo == ('eat', 'shelf'):
		# 	print(item1L1)
		# 	print(item1L2)
		# 	print(item1L3)
		# 	print(item2L1)
		# 	print(item2L2)
		# 	print(item2L3)
		# Check L1
		for L1_List in item1L1:
			c, c_l1, wt = L1_List
			if c_l1 == item2:
				eList.append([c, c_l1, wt])
				eList.append([c_l1, item2, wt])

		# L1 Not found. Check L2
		if not eList:
			for L2_List in item1L2:
				c, c_l1, c_l2, wt_l2 = L2_List
				wt_l1 = 0
				if c_l2 == item2:
					for L1_List in item1L1:
						if c_l1 == L1_List[1]:
							wt_l1 = L1_List[-1]
					eList.append([c, c_l1, wt_l1])
					eList.append([c_l1, c_l2, wt_l2])
					eList.append([c_l2, item2, wt_l2])

		# L2 Not found. Check L3
		if not eList:
			for L3_List in item1L3:
				c, c_l1, c_l2, c_l3, wt_l3 = L3_List
				wt_l1,wt_l2 = 0, 0

				if c_l3 == item2:
					for L2_List in item1L2:
						if c_l2 == L2_List[2]:
							wt_l2 = L2_List[-1]

					for L1_List in item1L1:
						if c_l1 == L1_List[1]:
							wt_l1 = L1_List[-1]
					eList.append([c, c_l1, wt_l1])
					eList.append([c_l1, c_l2, wt_l2])
					eList.append([c_l2, c_l3, wt_l3])
					# eList.append([c_l3, item2, wt_l3])

		edgeList[str(combo)] = eList

	with open(outFile, "w") as of:
		json.dump(edgeList, of, indent=4, sort_keys=True)

	return edgeList


grounded_gens = [('doorknob', 'photograph'), ('door', 'snuggle'), ('pillow', 'throw'), ('fix', 'laptop'), ('eat', 'shelf'), ('mirror', 'throw'), ('picture', 'pour'), ('couch', 'fix'), ('cook', 'vacuum'), ('box', 'wash'), ('bed', 'watch'), ('notebook', 'smile'), ('notebook', 'wash'), ('bottle', 'cook'), ('dish', 'lie'), ('floor', 'work'), ('pour', 'television'), ('mirror', 'take'), ('run', 'television'), ('notebook', 'take'), ('sneeze', 'window'), ('broom', 'hold'), ('refrigerator', 'take'), ('photograph', 'window'), ('broom', 'put'), ('food', 'laugh'), ('take', 'vacuum'), ('dish', 'photograph'), ('camera', 'play'), ('photograph', 'picture'), ('book', 'work'), ('book', 'walk'), ('camera', 'smile'), ('camera', 'laugh'), ('fix', 'hands'), ('medicine', 'take'), ('photograph', 'towel'), ('grasp', 'groceries'), ('refrigerator', 'work'), ('bed', 'snuggle'), ('bottle', 'play'), ('bottle', 'grasp'), ('awaken', 'groceries'), ('photograph', 'shoe'), ('bag', 'drink'), ('dress', 'light'), ('bed', 'wash'), ('make', 'picture'), ('laugh', 'notebook'), ('blanket', 'put'), ('broom', 'stand'), ('open', 'picture'), ('sit', 'window'), ('hands', 'tidy'), ('door', 'play'), ('chair', 'undress'), ('broom', 'fix'), ('hands', 'put'), ('laptop', 'throw'), ('mirror', 'photograph'), ('broom', 'sit'), ('hands', 'undress'), ('couch', 'grasp'), ('food', 'photograph'), ('take', 'towel'), ('clothes', 'hold'), ('laptop', 'make'), ('medicine', 'walk'), ('None', 'make'), ('drink', 'table'), ('hold', 'laptop'), ('vacuum', 'walk'), ('run', 'sandwich'), ('photograph', 'television'), ('book', 'tidy'), ('pour', 'sandwich'), ('bag', 'pour'), ('broom', 'dress'), ('box', 'dress'), ('mirror', 'talk'), ('bag', 'work'), ('awaken', 'bed'), ('doorway', 'grasp'), ('None', 'take'), ('cabinet', 'take'), ('grasp', 'refrigerator'), ('broom', 'close'), ('couch', 'snuggle'), ('hair', 'smile'), ('doorway', 'throw'), ('cook', 'dish'), ('shelf', 'talk'), ('doorknob', 'drink'), ('notebook', 'undress'), ('camera', 'snuggle'), ('drink', 'window'), ('food', 'smile'), ('chair', 'take'), ('groceries', 'tidy'), ('None', 'dress'), ('groceries', 'put'), ('floor', 'hold'), ('door', 'walk'), ('blanket', 'fix'), ('pillow', 'smile'), ('hands', 'pour'), ('box', 'tidy'), ('lie', 'window'), ('awaken', 'blanket'), ('bed', 'stand'), ('pour', 'towel'), ('cabinet', 'run'), ('shelf', 'sit'), ('cabinet', 'fix'), ('doorknob', 'sit'), ('cabinet', 'snuggle'), ('cabinet', 'turn'), ('food', 'undress'), ('put', 'window'), ('book', 'drink'), ('dress', 'laptop'), ('close', 'medicine'), ('photograph', 'refrigerator'), ('pillow', 'take'), ('groceries', 'work'), ('book', 'hold'), ('couch', 'sneeze'), ('sandwich', 'sit'), ('hair', 'stand'), ('None', 'tidy'), ('photograph', 'table'), ('floor', 'open'), ('broom', 'throw'), ('lie', 'mirror'), ('grasp', 'shoe'), ('shoe', 'watch'), ('doorway', 'fix'), ('chair', 'stand'), ('doorway', 'laugh'), ('open', 'television'), ('cabinet', 'wash'), ('hair', 'talk'), ('dress', 'vacuum'), ('stand', 'vacuum'), ('doorknob', 'smile'), ('box', 'drink'), ('shelf', 'smile'), ('bag', 'photograph'), ('table', 'undress'), ('notebook', 'photograph'), ('chair', 'talk'), ('lie', 'picture'), ('chair', 'smile'), ('bed', 'take'), ('groceries', 'play'), ('floor', 'pour'), ('dish', 'work'), ('picture', 'work'), ('dress', 'table'), ('laptop', 'snuggle'), ('medicine', 'photograph'), ('cabinet', 'hold'), ('None', 'eat'), ('cook', 'hair'), ('hair', 'hold'), ('camera', 'throw'), ('mirror', 'snuggle'), ('picture', 'undress'), ('blanket', 'undress'), ('run', 'towel'), ('groceries', 'run'), ('eat', 'shoe'), ('drink', 'towel'), ('cook', 'food'), ('clothes', 'grasp'), ('grasp', 'television'), ('clothes', 'play'), ('None', 'photograph'), ('doorway', 'stand'), ('drink', 'television'), ('laptop', 'sneeze'), ('cabinet', 'watch'), ('box', 'laugh'), ('eat', 'sandwich'), ('doorknob', 'lie'), ('None', 'open'), ('picture', 'sneeze'), ('medicine', 'pour'), ('floor', 'tidy'), ('dress', 'refrigerator'), ('door', 'wash'), ('None', 'lie'), ('chair', 'photograph'), ('book', 'cook'), ('snuggle', 'television'), ('couch', 'throw'), ('sandwich', 'snuggle'), ('blanket', 'lie'), ('bottle', 'watch'), ('hair', 'pour'), ('doorknob', 'open'), ('shelf', 'tidy'), ('laugh', 'refrigerator'), ('medicine', 'throw'), ('doorway', 'watch'), ('cabinet', 'photograph'), ('door', 'turn'), ('close', 'table'), ('floor', 'sit'), ('floor', 'smile'), ('notebook', 'put'), ('bag', 'put'), ('camera', 'close'), ('light', 'put'), ('doorway', 'talk'), ('snuggle', 'window'), ('broom', 'play'), ('close', 'pillow'), ('drink', 'laptop'), ('cabinet', 'cook'), ('bottle', 'put'), ('close', 'doorway'), ('None', 'hold'), ('chair', 'throw'), ('close', 'notebook'), ('book', 'take'), ('hair', 'snuggle'), ('laptop', 'stand'), ('cook', 'medicine'), ('turn', 'window'), ('awaken', 'light'), ('light', 'take'), ('chair', 'eat'), ('light', 'sit'), ('None', 'grasp'), ('clothes', 'work'), ('cabinet', 'laugh'), ('bag', 'open'), ('drink', 'floor'), ('medicine', 'turn'), ('notebook', 'sit'), ('doorknob', 'tidy'), ('food', 'make'), ('make', 'table'), ('clothes', 'tidy'), ('camera', 'photograph'), ('cabinet', 'undress'), ('box', 'play'), ('couch', 'put'), ('shoe', 'sit'), ('door', 'work'), ('sit', 'towel'), ('couch', 'watch'), ('dish', 'eat'), ('make', 'sandwich'), ('medicine', 'sit'), ('bottle', 'run'), ('mirror', 'sneeze'), ('bag', 'eat'), ('eat', 'groceries'), ('play', 'refrigerator'), ('make', 'notebook'), ('hands', 'play'), ('fix', 'window'), ('put', 'table'), ('cabinet', 'drink'), ('book', 'smile'), ('mirror', 'walk'), ('book', 'laugh'), ('hair', 'photograph'), ('doorknob', 'dress'), ('groceries', 'pour'), ('sandwich', 'sneeze'), ('refrigerator', 'tidy'), ('hands', 'talk'), ('lie', 'table'), ('couch', 'play'), ('hold', 'shoe'), ('box', 'smile'), ('medicine', 'open'), ('pillow', 'sneeze'), ('dish', 'run'), ('photograph', 'vacuum'), ('make', 'medicine'), ('dress', 'towel'), ('awaken', 'door'), ('sandwich', 'smile'), ('bag', 'tidy'), ('food', 'open'), ('close', 'shoe'), ('close', 'food'), ('clothes', 'take'), ('play', 'towel'), ('light', 'tidy'), ('notebook', 'stand'), ('grasp', 'light'), ('lie', 'sandwich'), ('laugh', 'medicine'), ('refrigerator', 'sneeze'), ('broom', 'undress'), ('camera', 'wash'), ('television', 'work'), ('chair', 'snuggle'), ('shelf', 'wash'), ('awaken', 'bag'), ('pillow', 'play'), ('cabinet', 'sit'), ('fix', 'mirror'), ('camera', 'watch'), ('hold', 'television'), ('sandwich', 'turn'), ('hair', 'lie'), ('cook', 'laptop'), ('bed', 'throw'), ('awaken', 'pillow'), ('couch', 'make'), ('fix', 'refrigerator'), ('book', 'lie'), ('medicine', 'sneeze'), ('bag', 'dress'), ('doorway', 'photograph'), ('light', 'play'), ('camera', 'turn'), ('bed', 'grasp'), ('dress', 'sandwich'), ('cook', 'door'), ('laptop', 'walk'), ('sneeze', 'television'), ('dish', 'put'), ('fix', 'groceries'), ('sandwich', 'take'), ('play', 'television'), ('awaken', 'mirror'), ('eat', 'television'), ('sit', 'vacuum'), ('camera', 'dress'), ('hands', 'smile'), ('box', 'lie'), ('box', 'cook'), ('chair', 'hold'), ('couch', 'smile'), ('picture', 'talk'), ('bottle', 'wash'), ('fix', 'notebook'), ('make', 'window'), ('broom', 'cook'), ('couch', 'eat'), ('hold', 'towel'), ('dish', 'watch'), ('camera', 'fix'), ('close', 'shelf'), ('television', 'watch'), ('couch', 'tidy'), ('bed', 'turn'), ('hold', 'picture'), ('table', 'talk'), ('doorknob', 'work'), ('dish', 'dress'), ('book', 'sneeze'), ('cabinet', 'stand'), ('notebook', 'pour'), ('picture', 'walk'), ('eat', 'table'), ('dress', 'television'), ('door', 'tidy'), ('awaken', 'dish'), ('clothes', 'turn'), ('doorknob', 'snuggle'), ('box', 'eat'), ('couch', 'walk'), ('doorway', 'make'), ('bed', 'sneeze'), ('pillow', 'walk'), ('vacuum', 'wash'), ('doorway', 'walk'), ('doorway', 'put'), ('cabinet', 'smile'), ('book', 'photograph'), ('broom', 'smile'), ('cabinet', 'sneeze'), ('put', 'sandwich'), ('close', 'groceries'), ('smile', 'television'), ('food', 'hold'), ('blanket', 'work'), ('awaken', 'sandwich'), ('floor', 'play'), ('clothes', 'dress'), ('pillow', 'put'), ('snuggle', 'vacuum'), ('chair', 'drink'), ('picture', 'put'), ('food', 'wash'), ('grasp', 'sandwich'), ('medicine', 'snuggle'), ('book', 'pour'), ('bottle', 'open'), ('doorknob', 'eat'), ('box', 'hold'), ('doorway', 'drink'), ('hair', 'watch'), ('chair', 'walk'), ('notebook', 'snuggle'), ('doorknob', 'pour'), ('bag', 'snuggle'), ('dress', 'pillow'), ('snuggle', 'table'), ('sneeze', 'vacuum'), ('dish', 'open'), ('bottle', 'walk'), ('doorway', 'run'), ('play', 'vacuum'), ('laugh', 'towel'), ('fix', 'shoe'), ('towel', 'watch'), ('put', 'television'), ('cook', 'hands'), ('clothes', 'smile'), ('shoe', 'tidy'), ('put', 'shelf'), ('chair', 'tidy'), ('laugh', 'shoe'), ('hair', 'turn'), ('notebook', 'sneeze'), ('bottle', 'throw'), ('floor', 'run'), ('picture', 'take'), ('box', 'pour'), ('towel', 'walk'), ('pour', 'shelf'), ('take', 'television'), ('hair', 'play'), ('dress', 'food'), ('grasp', 'medicine'), ('close', 'picture'), ('broom', 'lie'), ('door', 'stand'), ('doorway', 'take'), ('hold', 'shelf'), ('laptop', 'open'), ('clothes', 'make'), ('put', 'refrigerator'), ('doorknob', 'play'), ('table', 'work'), ('clothes', 'sit'), ('awaken', 'medicine'), ('eat', 'light'), ('bed', 'smile'), ('chair', 'laugh'), ('dish', 'fix'), ('awaken', 'camera'), ('camera', 'pour'), ('box', 'turn'), ('tidy', 'window'), ('hands', 'stand'), ('bottle', 'eat'), ('awaken', 'couch'), ('book', 'watch'), ('blanket', 'eat'), ('blanket', 'laugh'), ('hold', 'pillow'), ('laptop', 'run'), ('hair', 'run'), ('mirror', 'work'), ('None', 'talk'), ('make', 'refrigerator'), ('chair', 'open'), ('towel', 'undress'), ('drink', 'vacuum'), ('pillow', 'tidy'), ('food', 'watch'), ('doorknob', 'turn'), ('bag', 'smile'), ('walk', 'window'), ('medicine', 'tidy'), ('lie', 'pillow'), ('doorway', 'snuggle'), ('mirror', 'put'), ('blanket', 'open'), ('table', 'turn'), ('camera', 'put'), ('doorway', 'undress'), ('food', 'put'), ('grasp', 'pillow'), ('light', 'throw'), ('fix', 'floor'), ('bag', 'throw'), ('dress', 'mirror'), ('camera', 'eat'), ('notebook', 'throw'), ('groceries', 'sit'), ('doorway', 'wash'), ('broom', 'walk'), ('couch', 'photograph'), ('light', 'work'), ('bag', 'laugh'), ('cook', 'television'), ('sit', 'television'), ('table', 'take'), ('bottle', 'lie'), ('notebook', 'work'), ('dress', 'medicine'), ('chair', 'put'), ('awaken', 'chair'), ('floor', 'take'), ('cook', 'pillow'), ('clothes', 'photograph'), ('drink', 'refrigerator'), ('shelf', 'stand'), ('drink', 'shelf'), ('door', 'take'), ('bag', 'lie'), ('picture', 'run'), ('grasp', 'towel'), ('awaken', 'television'), ('refrigerator', 'snuggle'), ('pillow', 'watch'), ('None', 'run'), ('laptop', 'smile'), ('grasp', 'hands'), ('door', 'photograph'), ('television', 'walk'), ('camera', 'open'), ('clothes', 'talk'), ('hair', 'open'), ('door', 'talk'), ('close', 'hands'), ('door', 'throw'), ('couch', 'hold'), ('hair', 'work'), ('close', 'refrigerator'), ('open', 'refrigerator'), ('bottle', 'undress'), ('shelf', 'throw'), ('close', 'mirror'), ('hair', 'sneeze'), ('notebook', 'turn'), ('blanket', 'tidy'), ('light', 'snuggle'), ('cook', 'towel'), ('awaken', 'laptop'), ('blanket', 'pour'), ('door', 'smile'), ('hold', 'refrigerator'), ('floor', 'turn'), ('run', 'table'), ('laptop', 'play'), ('hair', 'undress'), ('chair', 'watch'), ('food', 'walk'), ('bag', 'walk'), ('None', 'sit'), ('table', 'throw'), ('close', 'hair'), ('dish', 'sneeze'), ('awaken', 'cabinet'), ('close', 'couch'), ('stand', 'television'), ('open', 'sandwich'), ('cabinet', 'work'), ('awaken', 'picture'), ('couch', 'sit'), ('floor', 'wash'), ('hands', 'watch'), ('picture', 'throw'), ('clothes', 'stand'), ('camera', 'stand'), ('awaken', 'vacuum'), ('hair', 'wash'), ('bed', 'dress'), ('groceries', 'smile'), ('blanket', 'turn'), ('groceries', 'make'), ('hands', 'open'), ('camera', 'sit'), ('clothes', 'pour'), ('door', 'run'), ('floor', 'grasp'), ('door', 'pour'), ('blanket', 'close'), ('bag', 'stand'), ('lie', 'notebook'), ('vacuum', 'work'), ('light', 'talk'), ('book', 'fix'), ('hold', 'light'), ('doorway', 'work'), ('awaken', 'refrigerator'), ('awaken', 'bottle'), ('bag', 'close'), ('wash', 'window'), ('chair', 'cook'), ('door', 'sneeze'), ('hair', 'throw'), ('laptop', 'undress'), ('dish', 'walk'), ('bed', 'hold'), ('bed', 'tidy'), ('awaken', 'broom'), ('picture', 'snuggle'), ('chair', 'fix'), ('None', 'cook'), ('awaken', 'shelf'), ('throw', 'towel'), ('dress', 'notebook'), ('grasp', 'window'), ('close', 'laptop'), ('door', 'fix'), ('couch', 'laugh'), ('groceries', 'watch'), ('awaken', 'floor'), ('fix', 'television'), ('shelf', 'walk'), ('bed', 'sit'), ('laugh', 'shelf'), ('bag', 'take'), ('cook', 'sandwich'), ('eat', 'mirror'), ('hair', 'take'), ('laptop', 'lie'), ('floor', 'snuggle'), ('shoe', 'wash'), ('bed', 'play'), ('fix', 'sandwich'), ('broom', 'open'), ('television', 'turn'), ('doorknob', 'talk'), ('cook', 'light'), ('clothes', 'wash'), ('cabinet', 'grasp'), ('doorway', 'pour'), ('grasp', 'vacuum'), ('cook', 'floor'), ('eat', 'notebook'), ('blanket', 'dress'), ('awaken', 'doorknob'), ('shelf', 'sneeze'), ('shelf', 'snuggle'), ('doorknob', 'grasp'), ('pillow', 'stand'), ('couch', 'drink'), ('laugh', 'window'), ('dish', 'undress'), ('None', 'put'), ('doorknob', 'throw'), ('dish', 'laugh'), ('clothes', 'drink'), ('grasp', 'laptop'), ('blanket', 'photograph'), ('bed', 'open'), ('open', 'towel'), ('watch', 'window'), ('sandwich', 'undress'), ('run', 'vacuum'), ('sandwich', 'talk'), ('medicine', 'smile'), ('shoe', 'talk'), ('pillow', 'talk'), ('notebook', 'tidy'), ('light', 'turn'), ('table', 'walk'), ('fix', 'vacuum'), ('bag', 'undress'), ('mirror', 'smile'), ('put', 'shoe'), ('groceries', 'undress'), ('light', 'undress'), ('laugh', 'vacuum'), ('doorknob', 'hold'), ('hands', 'turn'), ('eat', 'picture'), ('broom', 'tidy'), ('refrigerator', 'throw'), ('groceries', 'talk'), ('None', 'walk'), ('laptop', 'pour'), ('lie', 'television'), ('dish', 'take'), ('drink', 'food'), ('clothes', 'fix'), ('couch', 'wash'), ('clothes', 'snuggle'), ('door', 'make'), ('grasp', 'notebook'), ('broom', 'talk'), ('cabinet', 'play'), ('shelf', 'take'), ('photograph', 'shelf'), ('awaken', 'table'), ('dress', 'shelf'), ('laptop', 'watch'), ('mirror', 'play'), ('blanket', 'grasp'), ('None', 'undress'), ('clothes', 'cook'), ('hands', 'walk'), ('cook', 'mirror'), ('cabinet', 'make'), ('doorknob', 'sneeze'), ('clothes', 'sneeze'), ('medicine', 'talk'), ('book', 'wash'), ('notebook', 'open'), ('cook', 'doorway'), ('play', 'window'), ('light', 'walk'), ('box', 'stand'), ('door', 'hold'), ('awaken', 'book'), ('book', 'grasp'), ('laptop', 'put'), ('clothes', 'laugh'), ('undress', 'window'), ('mirror', 'tidy'), ('refrigerator', 'run'), ('dish', 'stand'), ('book', 'stand'), ('doorknob', 'stand'), ('cabinet', 'throw'), ('refrigerator', 'walk'), ('picture', 'tidy'), ('talk', 'television'), ('pillow', 'work'), ('blanket', 'cook'), ('pour', 'vacuum'), ('hair', 'laugh'), ('bed', 'lie'), ('chair', 'work'), ('make', 'shelf'), ('light', 'run'), ('cook', 'picture'), ('awaken', 'clothes'), ('cook', 'groceries'), ('book', 'talk'), ('drink', 'hair'), ('bottle', 'close'), ('bag', 'sneeze'), ('bottle', 'laugh'), ('hands', 'snuggle'), ('bed', 'close'), ('doorknob', 'watch'), ('light', 'sneeze'), ('light', 'wash'), ('bag', 'cook'), ('blanket', 'smile'), ('refrigerator', 'stand'), ('bottle', 'sneeze'), ('light', 'smile'), ('doorknob', 'take'), ('picture', 'stand'), ('clothes', 'throw'), ('laptop', 'work'), ('shoe', 'stand'), ('refrigerator', 'talk'), ('doorway', 'play'), ('light', 'photograph'), ('window', 'work'), ('close', 'dish'), ('food', 'stand'), ('smile', 'table'), ('camera', 'grasp'), ('put', 'towel'), ('open', 'shoe'), ('dish', 'turn'), ('box', 'work'), ('fix', 'picture'), ('shelf', 'watch'), ('book', 'sit'), ('bottle', 'snuggle'), ('floor', 'laugh'), ('bottle', 'fix'), ('camera', 'drink'), ('hair', 'sit'), ('shelf', 'turn'), ('hands', 'run'), ('refrigerator', 'watch'), ('floor', 'stand'), ('laugh', 'mirror'), ('laptop', 'wash'), ('hold', 'mirror'), ('cabinet', 'pour'), ('light', 'make'), ('fix', 'table'), ('shoe', 'throw'), ('fix', 'hair'), ('towel', 'work'), ('door', 'watch'), ('box', 'make'), ('bag', 'watch'), ('close', 'television'), ('awaken', 'shoe'), ('put', 'vacuum'), ('shoe', 'undress'), ('None', 'wash'), ('make', 'towel'), ('chair', 'grasp'), ('undress', 'vacuum'), ('dish', 'throw'), ('food', 'tidy'), ('doorknob', 'undress'), ('box', 'throw'), ('book', 'throw'), ('bag', 'talk'), ('blanket', 'sneeze'), ('couch', 'work'), ('blanket', 'stand'), ('medicine', 'put'), ('doorknob', 'wash'), ('chair', 'wash'), ('door', 'put'), ('blanket', 'hold'), ('book', 'make'), ('None', 'awaken'), ('bag', 'turn'), ('None', 'turn'), ('broom', 'pour'), ('photograph', 'pillow'), ('blanket', 'talk'), ('eat', 'window'), ('floor', 'walk'), ('blanket', 'wash'), ('bottle', 'hold'), ('groceries', 'photograph'), ('hands', 'throw'), ('talk', 'vacuum'), ('shelf', 'work'), ('book', 'dress'), ('notebook', 'walk'), ('refrigerator', 'turn'), ('door', 'laugh'), ('broom', 'drink'), ('broom', 'eat'), ('close', 'light'), ('doorknob', 'laugh'), ('refrigerator', 'undress'), ('laptop', 'photograph'), ('shoe', 'walk'), ('door', 'drink'), ('bed', 'cook'), ('book', 'run'), ('sandwich', 'work'), ('doorway', 'sit'), ('food', 'talk'), ('pillow', 'undress'), ('awaken', 'food'), ('hands', 'hold'), ('eat', 'towel'), ('camera', 'take'), ('open', 'table'), ('hold', 'sandwich'), ('bed', 'eat'), ('None', 'watch'), ('shoe', 'smile'), ('None', 'throw'), ('laptop', 'talk'), ('book', 'play'), ('smile', 'window'), ('groceries', 'stand'), ('open', 'shelf'), ('floor', 'undress'), ('broom', 'watch'), ('drink', 'sandwich'), ('couch', 'open'), ('vacuum', 'watch'), ('throw', 'vacuum'), ('camera', 'tidy'), ('cook', 'couch'), ('None', 'smile'), ('laugh', 'pillow'), ('eat', 'medicine'), ('light', 'pour'), ('medicine', 'wash'), ('notebook', 'talk'), ('groceries', 'laugh'), ('bed', 'work'), ('shelf', 'undress'), ('door', 'sit'), ('chair', 'pour'), ('sandwich', 'tidy'), ('hands', 'make'), ('dish', 'snuggle'), ('blanket', 'take'), ('couch', 'dress'), ('bottle', 'pour'), ('book', 'put'), ('bag', 'fix'), ('drink', 'picture'), ('medicine', 'play'), ('lie', 'shoe'), ('photograph', 'sandwich'), ('laugh', 'picture'), ('awaken', 'doorway'), ('bottle', 'stand'), ('doorway', 'sneeze'), ('grasp', 'shelf'), ('food', 'pour'), ('cook', 'notebook'), ('bed', 'make'), ('throw', 'window'), ('dish', 'sit'), ('groceries', 'take'), ('doorway', 'hold'), ('box', 'put'), ('picture', 'wash'), ('table', 'watch'), ('tidy', 'towel'), ('play', 'sandwich'), ('turn', 'vacuum'), ('box', 'take'), ('hair', 'put'), ('refrigerator', 'smile'), ('blanket', 'walk'), ('cabinet', 'put'), ('table', 'wash'), ('picture', 'watch'), ('camera', 'cook'), ('groceries', 'snuggle'), ('mirror', 'wash'), ('doorknob', 'put'), ('door', 'undress'), ('box', 'close'), ('clothes', 'undress'), ('floor', 'sneeze'), ('food', 'snuggle'), ('bottle', 'drink'), ('groceries', 'walk'), ('camera', 'lie'), ('bottle', 'talk'), ('fix', 'food'), ('laugh', 'television'), ('None', 'snuggle'), ('eat', 'hair'), ('book', 'eat'), ('food', 'lie'), ('cabinet', 'talk'), ('chair', 'make'), ('fix', 'shelf'), ('lie', 'light'), ('hands', 'take'), ('book', 'turn'), ('chair', 'run'), ('picture', 'sit'), ('box', 'talk'), ('bed', 'photograph'), ('groceries', 'wash'), ('light', 'watch'), ('clothes', 'lie'), ('pillow', 'wash'), ('bottle', 'photograph'), ('broom', 'wash'), ('open', 'pillow'), ('doorknob', 'fix'), ('couch', 'take'), ('eat', 'laptop'), ('laptop', 'tidy'), ('sandwich', 'throw'), ('cook', 'table'), ('doorknob', 'run'), ('food', 'throw'), ('hair', 'walk'), ('None', 'play'), ('run', 'shoe'), ('drink', 'groceries'), ('tidy', 'vacuum'), ('blanket', 'snuggle'), ('camera', 'talk'), ('clothes', 'open'), ('food', 'grasp'), ('food', 'play'), ('blanket', 'make'), ('laptop', 'sit'), ('notebook', 'run'), ('pour', 'table'), ('grasp', 'hair'), ('box', 'undress'), ('chair', 'play'), ('grasp', 'table'), ('fix', 'medicine'), ('bottle', 'dress'), ('box', 'sit'), ('medicine', 'watch'), ('shoe', 'turn'), ('dress', 'hands'), ('medicine', 'work'), ('sandwich', 'wash'), ('couch', 'turn'), ('open', 'window'), ('laugh', 'table'), ('clothes', 'eat'), ('close', 'door'), ('hands', 'wash'), ('floor', 'watch'), ('dish', 'hold'), ('drink', 'light'), ('groceries', 'lie'), ('television', 'undress'), ('awaken', 'hands'), ('dress', 'shoe'), ('clothes', 'run'), ('laugh', 'light'), ('eat', 'hands'), ('bottle', 'sit'), ('television', 'wash'), ('floor', 'make'), ('dish', 'tidy'), ('food', 'turn'), ('make', 'mirror'), ('blanket', 'throw'), ('bottle', 'make'), ('bag', 'run'), ('food', 'run'), ('laugh', 'sandwich'), ('cook', 'refrigerator'), ('lie', 'medicine'), ('snuggle', 'towel'), ('blanket', 'drink'), ('cabinet', 'close'), ('door', 'grasp'), ('chair', 'dress'), ('table', 'tidy'), ('picture', 'turn'), ('broom', 'take'), ('bed', 'pour'), ('box', 'fix'), ('grasp', 'mirror'), ('food', 'sneeze'), ('talk', 'window'), ('refrigerator', 'sit'), ('chair', 'close'), ('picture', 'play'), ('bottle', 'smile'), ('couch', 'undress'), ('shoe', 'take'), ('play', 'shelf'), ('close', 'clothes'), ('bed', 'run'), ('play', 'shoe'), ('food', 'take'), ('clothes', 'walk'), ('eat', 'vacuum'), ('sit', 'table'), ('camera', 'walk'), ('refrigerator', 'wash'), ('pour', 'window'), ('medicine', 'undress'), ('lie', 'shelf'), ('None', 'close'), ('shoe', 'work'), ('pillow', 'pour'), ('notebook', 'watch'), ('camera', 'make'), ('laptop', 'laugh'), ('cook', 'shoe'), ('shoe', 'sneeze'), ('sandwich', 'walk'), ('broom', 'work'), ('blanket', 'run'), ('broom', 'turn'), ('bed', 'talk'), ('None', 'stand'), ('book', 'undress'), ('None', 'work'), ('hands', 'photograph'), ('couch', 'lie'), ('groceries', 'throw'), ('dish', 'pour'), ('notebook', 'play'), ('None', 'laugh'), ('dress', 'picture'), ('pour', 'shoe'), ('doorknob', 'make'), ('mirror', 'open'), ('broom', 'run'), ('door', 'eat'), ('bag', 'play'), ('doorknob', 'walk'), ('eat', 'floor'), ('box', 'open'), ('broom', 'sneeze'), ('doorway', 'smile'), ('drink', 'mirror'), ('hands', 'sneeze'), ('box', 'grasp'), ('camera', 'run'), ('bed', 'put'), ('box', 'watch'), ('grasp', 'picture'), ('close', 'window'), ('floor', 'talk'), ('dish', 'grasp'), ('fix', 'light'), ('make', 'pillow'), ('mirror', 'undress'), ('box', 'photograph'), ('groceries', 'hold'), ('blanket', 'play'), ('pillow', 'turn'), ('door', 'open'), ('fix', 'towel'), ('box', 'walk'), ('mirror', 'turn'), ('dish', 'wash'), ('mirror', 'pour'), ('drink', 'hands'), ('doorway', 'eat'), ('door', 'dress'), ('drink', 'shoe'), ('couch', 'run'), ('dish', 'drink'), ('cabinet', 'lie'), ('drink', 'notebook'), ('doorway', 'lie'), ('box', 'snuggle'), ('cook', 'shelf'), ('dish', 'talk'), ('make', 'vacuum'), ('smile', 'towel'), ('pour', 'refrigerator'), ('drink', 'pillow'), ('shoe', 'snuggle'), ('bag', 'sit'), ('towel', 'turn'), ('blanket', 'watch'), ('dress', 'groceries'), ('camera', 'work'), ('cabinet', 'open'), ('make', 'shoe'), ('groceries', 'sneeze'), ('doorway', 'open'), ('play', 'table'), ('cook', 'doorknob'), ('awaken', 'towel'), ('fix', 'pillow'), ('sneeze', 'table'), ('awaken', 'window'), ('box', 'sneeze'), ('awaken', 'box'), ('cabinet', 'tidy'), ('cook', 'window'), ('hold', 'vacuum'), ('eat', 'refrigerator'), ('hands', 'work'), ('bottle', 'turn'), ('towel', 'wash'), ('hold', 'notebook'), ('lie', 'towel'), ('dish', 'smile'), ('cabinet', 'eat'), ('door', 'lie'), ('light', 'open'), ('chair', 'turn'), ('box', 'run'), ('mirror', 'watch'), ('talk', 'towel'), ('couch', 'pour'), ('bag', 'wash'), ('close', 'vacuum'), ('sneeze', 'towel'), ('book', 'open'), ('dress', 'floor'), ('open', 'vacuum'), ('hold', 'table'), ('bed', 'undress'), ('awaken', 'hair'), ('take', 'window'), ('bag', 'grasp'), ('television', 'tidy'), ('broom', 'make'), ('drink', 'medicine'), ('hands', 'sit'), ('bottle', 'take'), ('smile', 'vacuum'), ('bed', 'drink'), ('picture', 'smile'), ('pillow', 'snuggle'), ('doorway', 'tidy'), ('close', 'doorknob'), ('floor', 'lie'), ('blanket', 'sit'), ('hold', 'window'), ('sandwich', 'stand'), ('floor', 'put'), ('doorway', 'turn'), ('broom', 'grasp'), ('bed', 'fix'), ('dish', 'play'), ('chair', 'sit'), ('book', 'snuggle'), ('close', 'sandwich'), ('stand', 'window'), ('dish', 'make'), ('floor', 'photograph'), ('eat', 'pillow'), ('None', 'sneeze'), ('broom', 'photograph'), ('television', 'throw'), ('run', 'shelf'), ('chair', 'lie'), ('lie', 'vacuum'), ('run', 'window'), ('couch', 'talk'), ('close', 'floor'), ('cabinet', 'dress'), ('laptop', 'take'), ('groceries', 'open'), ('bed', 'walk'), ('doorway', 'dress'), ('food', 'sit'), ('medicine', 'run'), ('pillow', 'run'), ('None', 'pour'), ('mirror', 'sit'), ('make', 'television'), ('mirror', 'run'), ('stand', 'table'), ('pillow', 'sit'), ('mirror', 'stand'), ('close', 'towel'), ('dress', 'hair'), ('bag', 'make'), ('bottle', 'tidy'), ('hands', 'laugh'), ('chair', 'sneeze'), ('camera', 'hold'), ('clothes', 'watch'), ('book', 'close'), ('bottle', 'work'), ('camera', 'sneeze'), ('broom', 'laugh'), ('lie', 'refrigerator'), ('broom', 'snuggle'), ('hair', 'tidy'), ('dress', 'window'), ('bag', 'hold'), ('sandwich', 'watch'), ('eat', 'food'), ('laptop', 'turn'), ('floor', 'throw'), ('hold', 'medicine'), ('groceries', 'turn'), ('food', 'work'), ('couch', 'stand'), ('None', 'drink'), ('stand', 'towel'), ('awaken', 'notebook'), ('None', 'fix'), ('clothes', 'put'), ('camera', 'undress'), ('light', 'stand'), ('medicine', 'stand'), ('cabinet', 'walk'), ('hands', 'lie'), ('bed', 'laugh')]

generate = False

if generate:
	DirectDict = getDirectDict(grounded_gens)
	L1Dict = getL1Dict(grounded_gens)
	L1_List = []
	for key,values in L1Dict.iteritems():
		for value in values:
			L1_List.append(value)

	L2Dict = getL2Dict(L1_List, "./L2Dict.json")

	L2_List = []
	for key,values in L2Dict.iteritems():
		for value in values:
			L2_List.append(value)

	L3Dict = getL3Dict(L2_List, "./L3Dict.json")

else:
	DirectDict = json.load(open('./DirectDict.json'))
	L1Dict = json.load(open('./L1Dict.json'))
	L2Dict = json.load(open('./L2Dict.json'))
	L3Dict = json.load(open('./L3Dict.json'))


cues = constructCues(grounded_gens, L1Dict, L2Dict, L3Dict, './Cues.json' )