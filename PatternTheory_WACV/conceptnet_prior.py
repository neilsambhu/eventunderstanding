import json
import urllib2
import numpy as np

def act_obj(actions, actions_ori, objects, objects_ori, filename):
	act_obj_mat = np.zeros((len(actions), len(objects)))
	target = open(filename, 'w')
	print("writing to file\n");
	for a in range(0,len(actions)):
		target.write(actions_ori[a] + ",")
		for b in range(0,len(objects)):
			target.write(objects_ori[b])
			target.write(":")
					
			if a != b:
				concept1 = "/c/en/"  + actions[a]
				concept2 = "/c/en/" + objects[b]
				CNUrl = "http://conceptnet5.media.mit.edu/data/5.4/assoc" + concept1 + "?filter=" + concept2 + "/.&limit=1"			
				#print(CNUrl)
				try:
					response = urllib2.urlopen(CNUrl)
					content = json.load(urllib2.urlopen(CNUrl))
				except urllib2.HTTPError, e:
					if e.getcode() == 500:
						content = e.read()
				# print(content)
				if len(content['similar']) > 0:
					#print((content['similar'][0][1]))
					act_obj_mat[a, b] = content['similar'][0][1] * 100
					
			target.write(str(act_obj_mat[a, b]))
			if(b<len(objects)):
				target.write(",")

		target.write("\n")

	target.close()
	print(act_obj_mat)

def act_act(actions, actions_ori, filename):
	act_act_mat = np.zeros((len(actions), len(actions)))
	target = open(filename, 'w')
	print("writing to file\n");
	for a in range(0,len(actions)):
		target.write(actions_ori[a] + ",")
		for b in range(0,len(actions)):
			target.write(actions_ori[b])
			target.write(":")
					
			if a != b:
				concept1 = "/c/en/"  + actions[a]
				concept2 = "/c/en/" + actions[b]
				CNUrl = "http://conceptnet5.media.mit.edu/data/5.4/assoc" + concept1 + "?filter=" + concept2 + "/.&limit=1"			
				#print(CNUrl)
				try:
					response = urllib2.urlopen(CNUrl)
					content = json.load(urllib2.urlopen(CNUrl))
				except urllib2.HTTPError, e:
					if e.getcode() == 500:
						content = e.read()
				# print(content)
				if len(content['similar']) > 0:
					#print((content['similar'][0][1]))
					act_act_mat[a, b] = content['similar'][0][1] * 100
					
			target.write(str(act_act_mat[a, b]))
			if(b<len(actions)):
				target.write(",")

		target.write("\n")

	target.close()
	print(act_act_mat)

def obj_obj(objects, objects_ori, filename):
	obj_obj_mat = np.zeros((len(objects), len(objects)))
	target = open(filename, 'w')
	print("writing to file\n");
	for a in range(0,len(objects)):
		target.write(objects_ori[a] + ",")
		for b in range(0,len(objects)):
			target.write(objects_ori[b])
			target.write(":")
					
			if a != b:
				concept1 = "/c/en/"  + objects[a]
				concept2 = "/c/en/" + objects[b]
				CNUrl = "http://conceptnet5.media.mit.edu/data/5.4/assoc" + concept1 + "?filter=" + concept2 + "/.&limit=1"			
				#print(CNUrl)
				try:
					response = urllib2.urlopen(CNUrl)
					content = json.load(urllib2.urlopen(CNUrl))
				except urllib2.HTTPError, e:
					if e.getcode() == 500:
						content = e.read()
				# print(content)
				if len(content['similar']) > 0:
					#print((content['similar'][0][1]))
					obj_obj_mat[a, b] = content['similar'][0][1] * 100
					
			target.write(str(obj_obj_mat[a, b]))
			if(b<len(objects)):
				target.write(",")

		target.write("\n")

	target.close()
	print(obj_obj_mat)

#import requests
actions = ["cut","walk_in","spoon","peel","stir","walk_out", "smear","put","squeeze", "butter", "pour", "fry", "crack", "take", "add"]
actions_ori = ["cut-a","walkin-a","spoon-a","peel-a","stir-a","walkout-a", "smear-a","put-a","squeeze-a", "butter-a", "pour-a", "fry-a", "crack-a", "take-a", "add-a"]
objects = ["topping", "topping_on_top", "coffee", "teabag", "plate", "eggs", "juice", "salt_and_pepper", "milk", "powder", "bun_together", "fruit", "tea", "pancake", "cereals", "sugar", "bun", "bowl", "egg", "glass", "water", "orange", "pan", "cup", "oil", "dough", "flour", "squeezer", "butter", "knife"]
objects_ori = ["topping-o", "toppingOnTop-o", "coffee-o", "teabag-o", "plate-o", "eggs-o", "juice-o", "saltnpepper-o", "milk-o", "powder-o", "bunTogether-o", "fruit-o", "tea-o", "pancake-o", "cereals-o", "sugar-o", "bun-o", "bowl-o", "egg-o", "glass-o", "water-o", "orange-o", "pan-o", "cup-o", "oil-o", "dough-o", "flour-o", "squeezer-o", "butter-o", "knife-o"]
#actions = ["stir", "flip", "pour", "pick_up", "season", "put_down"]

actions = ["stir", "crack", "spray", "twist", "take", "pour", "open", "switch", "walk", "put", "close", "read"]
objects = ["baking_pan", "bowl", "box", "bag", "egg", "fork", "measuring_cup", "oil", "pan", "scissors", "fridge", "oven", "cap", "knife"]
objects_ori = ["baking_pan", "bowl", "brownie_box", "brownie_bag", "egg", "fork", "measuring_cup", "oil", "baking_pan", "scissors", "fridge", "oven", "cap", "knife"]

print len(objects), len(actions)
filename = "conceptnet_breakfast_actions_objects_100_Similarity.txt"

act_obj(actions, actions, objects, objects_ori, filename)


# concept1 = "/c/en/oil/"
# concept2 = "/c/en/whisk/"
# CNUrl = "http://conceptnet5.media.mit.edu/data/5.4/assoc" + concept1 + "?filter=" + concept2 + ".&limit=1"
# print(CNUrl)

# try:
#   response = urllib2.urlopen(CNUrl)
#   content = json.load(urllib2.urlopen(CNUrl))
# except urllib2.HTTPError, e:
#   if e.getcode() == 500:
#     content = e.read()
#   else:
#     raise
# print(content)

# print(len(content['similar']))

#data = {}
#response = requests.get(url, data=data)