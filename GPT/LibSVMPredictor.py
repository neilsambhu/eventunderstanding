#!/usr/bin/python

from Predictor import *
import string
import os
import glob
import random


class LibSVMPredictor(Predictor):
    # params
    def __init__(self,method,feature,models_filename,labels_filename,program_path,params='-b 1'):
        super(LibSVMPredictor,self).__init__(method,feature)
        self.__program_path = program_path
        self.__params = params
        self.__models = {}
        self.__read_models(models_filename)
        self.__labels_id = {}
        self.__read_labels(labels_filename)

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

    def __avg(self,elements):
        sum = 0.0
        n = len(elements)
        for value in elements:
            sum += float(value)
        return (sum/n)

    def __max(self,elements,k):
        score = 0.0
        n = k
        if k > len(elements):
            n = len(elements)
        elements.sort(reverse=True)
        for i in range(n):
            score += elements[i]
        score = score / n

        return score

    def	__min(self,elements):
        min_index = 0
        min_value = elements[min_index]
        n = len(elements)
        for i in range(1,n):
            if elements[i] < min_value:
                min_value = elements[i]
        return min_value

    # modes: 'max', 'avg', 'mod', 'min', 'top'
    def __read_scores(self,label,filename,mode='max',k=1):
        label_index = None
        target = self.__labels_id[label]

        file = open(filename)

        line = file.readline()
        headline_content = string.split(line.replace('\n',''))
        for i in range(1,len(headline_content)):
            if int(headline_content[i]) == target:
                label_index = i
                break

        if label_index == None:
            return 0.0001 # or we could just return 0.0

        scores = []
        for line in file:
            instance_predictions = string.split(line.replace('\n',''))
            scores.append(float(instance_predictions[label_index]))

        file.close()

        if mode == 'max':
            return self.__max(scores,k)
        elif mode == 'avg':
            return self.__avg(scores)
        elif mode == 'min':
            return self.__min(scores)

        # default treatment
        return self.__max(scores,k)

    def __majority_voting_predictor(self,input_path,extension='cnn'):
        # Concatenate the files
        file_list = glob.glob(input_path + '/*.' + extension);
        keyname = input_path.split('/')[-1];
        with open(str(os.getpid())+'_'+keyname+'.cnn','w') as wfp:
            for filename in file_list:
                with open(filename) as rfp:
                    for line in rfp:
                        wfp.write(line);




    def run(self,label_name,g,mode='silent'):
        model_name = label_name + g.get_name()
        #print 'model name: ',model_name
        if g.get_features() == None:
            return 0.0001
        elif model_name not in self.__models:
            return 0.0001

        # stub (just for testing purposes):
        #	return random.uniform(0,1)

        #	output_scores = g.get_name() + '_' + repr(g.get_id()) + '_' + label_name + '.scores'
        #output_scores = g.get_name() + '_' + repr(g.get_id()) + '.scores' ## for ICPR2014
        feature_filename = g.get_features().split('/')[-1]
        #output_scores = feature_filename + '_' + label_name + '.scores'
        output_scores = str(os.getpid()) + '_' + label_name + '_' + feature_filename + '.scores'
        if os.path.isfile(output_scores):
            #print output_scores
            score = self.__read_scores(label_name, output_scores)
            #if score > 0.95:
            #    score = 0.95
            return score
        else:
            model = self.__models[model_name]
            feature_file = g.get_features()

            # rescaling the features to numeric range of the model
            range_filename = '/'.join(model.strip().split('/')[0:-1])+'/'+label_name+'.range'
            cmdline = self.__program_path + '/svm-scale -r ' + range_filename + ' ' + feature_file + ' > ' + \
                      feature_file + '.' + label_name + '.scaled.' + str(os.getpid())
            #print cmdline
            os.system(cmdline)
            #os.system(self.__program_path + '/svm-scale -r ' + range_filename + ' ' + feature_file +  ' > ' + feature_file + '.' + label_name + '.scaled')

            cmdline = self.__program_path
            cmdline += '/svm-predict '
            cmdline += self.__params + ' '
            cmdline += feature_file + '.' + label_name + '.scaled.' + str(os.getpid())
            cmdline += ' ' + model + '  ' + output_scores

            if mode == 'silent':
                cmdline += ' > LibSVMPredictor.run.log'
            #print cmdline
            elif mode == 'verbose':
                print cmdline
#            print 'execute: '+cmdline
            os.system(cmdline)
            tmp_file = feature_file + '.' + label_name + '.scaled.' + str(os.getpid())
            os.system('rm ' + tmp_file)

            score = self.__read_scores(label_name,output_scores)
            #if score > 0.95:
            #    score = 0.95
            return score
