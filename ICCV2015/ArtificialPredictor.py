#!/usr/bin/python

from Feature import *
from Predictor import *
import string
import os
import random
import copy

class ArtificialPredictor(Predictor):
    # params
    # method: 'random', 'degradation', 'rank', 
    def __init__(self,generator_space_filename,features_filename,method='degradation',error_rate=0.0,rank=1,proc=1):
        random.seed(12345)
        self.__method = method
        self.__error_rate = error_rate
        self.__rank = rank
        self.__features = []
        self.__proc = proc
        self.__setup_predictor(generator_space_filename,features_filename)
        self.__confusion_matrix_filename = 'cm_' + method + '_er' + repr(int(error_rate*100)) + '_r' + repr(rank) + '.txt'


    def __setup_predictor(self, gspace_filename, features_filename):
        self.__read_feature_file(features_filename)

        # collect known feature types
        feature_types = {}
        for f in self.__features:
            if f.name not in feature_types:
                feature_types[f.name] = []

        # organize concept labels per feature type
        # have to change this code to consider modality
        file = open(gspace_filename)
        for line in file:
            data = string.split(line.replace('\n',''))
            bonds = None
            if len(data) > 2:
                bonds = string.split(data[2],',')
                labels = []
                for b in bonds:
                    labels.append(b.split(':')[0])

                for t in feature_types:
                    if t in labels:
                        feature_types[t].append(data[0])
                         #						print repr(feature_types[t])
        file.close()

        n = len(self.__features)
        m = int(round(self.__error_rate * n))
        indices = []
        if m > 0:
            indices = random.sample(range(n),m)

        for i in range(len(self.__features)):
            names = string.split(self.__features[i].path,'/')
            idname = names[len(names)-1]

            #output_score_filename = str(self.__proc) + '_' + idname + '.scores'
            output_score_filename = str(self.__error_rate) + '_' + idname + '.scores'
            if os.path.isfile(output_score_filename):
                continue

            #print output_score_filename
            # open write file to store the scores for each label
            outfile = open(output_score_filename,'w')

            # collect all possible labels for the target features
            labels = copy.deepcopy(feature_types[self.__features[i].name])

            # keep track of the ground-truth label
            correct_label = self.__features[i].label[0]

            if i in indices:
                # print correct_label + ',' + repr(random.uniform(0.60,0.75))
                outfile.write(correct_label + ',' + repr(random.uniform(0.74,0.75)) + '\n')

                if correct_label in labels:
                    labels.remove(correct_label)
                #print 'labels: ' + repr(labels)

                ranked_labels = random.sample(range(1,len(labels)+1),len(labels))
                #print 'label ranks: ' + repr(ranked_labels)

                for k in range(len(labels)):
                    if ranked_labels[k] < self.__rank:
                        outfile.write(labels[k] + ',' + repr(random.uniform(0.8,0.9)) + '\n')
                    else:
                        outfile.write(labels[k] + ',' + repr(random.uniform(0.01,0.4)) + '\n')
            else:
                outfile.write(correct_label + ',' + repr(random.uniform(0.74,0.75)) + '\n')
                for k in range(len(labels)):
                    if labels[k] != correct_label:
                        outfile.write(labels[k] + ',' + repr(random.uniform(0.01,0.4)) + '\n')
            outfile.close()

    def __read_feature_file(self,filename):
        cost = 20
        file = open(filename)
        for line in file:
            data = string.split(line.replace('\n',''))
            labels = string.split(data[3],',')
            feature_location = None
            if len(data) > 4:
                feature_location = data[4]
            self.__features.append(Feature(data[0],data[2],int(data[1]),cost,labels,feature_location))
        file.close()

    def __read_models(self,filename):
        file = open(filename)
        for line in file:
            data = string.split(line.replace('\n',''))
            if len(data) > 2:
                model_name = data[0] + data[1]
                self.__models[model_name] = data[2]
        file.close()

    def __read_labels(self,filename):
        file = open(filename)
        for line in file:
            data = string.split(line.replace('\n',''))
            self.__labels_id[data[0]] = int(data[1])
        file.close()

    # modes: 'max', 'avg', 'mod', 'min', 'top'
    def __read_scores(self,label,filename):
        #print 'searched label: ',label
        file = open(filename)
        for line in file:
            data = string.split(line.replace('\n',''),',')
            #print repr(data)
            if data[0] == label:
                #print 'found'
                file.close()
                return float(data[1])

    def run(self,label_name,g,mode='verbose'):
        if self.__method == 'random':
            return random.uniform(0,1)
        elif self.__method == 'degradation':
            feature_path = g.get_features()
            names = string.split(feature_path,'/')
            idname = names[len(names)-1]
            #output_score_filename = str(self.__proc) + '_' + idname + '.scores'
            output_score_filename = str(self.__error_rate) + '_' + idname + '.scores'
            #			print 'inside predict'
            return self.__read_scores(label_name,output_score_filename)
