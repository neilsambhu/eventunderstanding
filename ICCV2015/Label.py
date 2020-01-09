#!/usr/bin/python

class Label:
	
	def __init__(self,name,modality,level,score,g_id,cost):
		self.name = name			# label name
		self.modality = modality   	# a vector with one or more modalities
		self.level = level			# hierarchy level of the label
		self.score = score			#
		self.g_id = g_id
		self.cost = cost
		