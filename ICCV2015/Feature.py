#!/usr/bin/python

class Feature:

    def __init__(self,name,path,time,cost,label,location,box):
        self.name = name
        self.path = path
        self.time = time
        self.cost = cost
        self.label = label
        self.location = location
        self.box_location = box
