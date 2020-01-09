#!/usr/bin/python

import os
import re
import glob
import string
from FeatureHandler import *
from operator import itemgetter

def recursive_file_search(path_list=[],file_list=[],file_extension=[]):
    item_list = []
    if not path_list:
        return (path_list,file_list)
    for path in path_list:
        for item in glob.glob(path + '/*'):
            if os.path.isdir(item) == True and item.split('/')[-1] not in ['.','..']:
                item_list.append(item)
            else:
                for extension in file_extension:
                    if item.endswith(extension) == True:
                        file_list.append(item)
                    
    return recursive_file_search(item_list,file_list,file_extension)

def concat_files(ordered_file_list,output_filename='concat_result.txt'):
    with open(output_filename, 'a') as outfile:
        for fname in ordered_file_list:
            with open(fname) as infile:
                for line in infile:
                    outfile.write(line)


def prepare_fold_codebook_features(training_path, output_path):
    path_list = []
    for path in glob.glob(training_path + '/*'):
        path_list.append(path.split('/')[-1])
        
    number_of_folds = len(path_list)    
    for fold in path_list:
        fold_path = output_path + '/fold_' + fold
        print 'processing for ' + fold_path
        if os.path.isdir(fold_path) == False:
            os.system( 'mkdir ' + fold_path )
        
        if os.path.isdir(fold_path + '/codebook') == False:    
            os.system( 'mkdir ' + fold_path + '/codebook' )
        
        for training_fold in path_list:
            if training_fold != fold: 
                training_fold_path = training_path + '/' + training_fold
                for concept_path in glob.glob(training_fold_path + '/*'):
                    name = concept_path.split('/')[-1]
                    if os.path.isdir(fold_path + '/codebook/' + name) == False:
                        os.system('mkdir ' + fold_path + '/codebook/' + name)
                    for concept_file in glob.glob(concept_path + '/*'):
                        output_concept_filename = fold_path + '/codebook/' + name + '/' + concept_file.split('/')[-1] 
                        print output_concept_filename
                        concat_files([concept_file],output_concept_filename)
                        
def convert_to_numeric_vector(string_list):
    numeric_vector = []
    for i in range(len(string_list)):
        numeric_vector.append(float(string_list[i]))
    return numeric_vector


def prepare_test_features(k,input_path,output_path,code=[0,16,29,42,53]):
    frame_number_column = 6

    feature_file_list = []
    recursive_file_search([input_path], feature_file_list, ['_stipdet.txt'])
    #print 'number of feature files: ' + repr(len(feature_file_list))

    if os.path.isdir(output_path) == False:
        os.system('mkdir ' + output_path)
    if os.path.isdir(output_path + '/s' + str(k)) == False:
        os.system('mkdir ' + output_path + '/s' + str(k))

    features = []
    for feature_file in feature_file_list:
        filename = feature_file.split('/')[-1]
	#os.system('wc -l '+feature_file)
        subject = filename.split('_')[0]
        subject_id = int(subject.split('P')[1])
        if subject_id < code[k-1] or subject_id >= code[k]:
            continue

        cam = feature_file.split('/')[-2]
        activity = filename.split('_')[1]

        #count = 0
        new_filename = subject + '_' + activity + '_' + cam + '.hofhog' 
        file = open(feature_file,'r')
        for line in file:
            #count += 1
            if not line.startswith('#'):
                feature_vector = convert_to_numeric_vector(line.strip().split())
                features.append(feature_vector)
                #file.write(line)
        file.close()

        #print '# of lines: '+repr(count)

        features.sort(key=itemgetter(frame_number_column))
        file = open(output_path + '/s' + str(k) + '/' + new_filename,'w')
        for feature in features:
            file.write(str(feature[0]))
            for i in range(1,len(feature)):
                file.write(' '+str(feature[i]))
            file.write('\n')        
        file.close()
        del features[:]
  
def construct_training_histograms(training_path='../features', output_path='..', codebook_root_path='../experiments', program_path='./GMMBoVW', libsvm=False, class_label=0, temporal_window_size=5):
    tsz = temporal_window_size
    path_list = []
    for path in glob.glob(training_path + '/*'):
        path_list.append(path.split('/')[-1])
    
    if os.path.isdir(output_path + '/histogram') == False:
        os.system( 'mkdir ' + output_path + '/histogram')
    output_path += '/histogram'
        
    number_of_folds = len(path_list)    
    for fold in path_list:
        fold_path = output_path + '/fold_' + fold
        if os.path.isdir(fold_path) == False:
            os.system('mkdir '+fold_path)

        codebook_path = codebook_root_path + '/fold_' + fold + '/codebook'
        print 'processing for ' + fold_path
        
        #if os.path.isdir(fold_path + '/histogram') == False:    
        #    os.system( 'mkdir ' + fold_path + '/histogram' )
         
        features = []
        for training_fold in path_list:
            if training_fold != fold: 
                training_fold_path = training_path + '/' + training_fold
                # for each feature file
                for feature_file in glob.glob(training_fold_path + '/*'):
                    # parse the file name -- it shows which concepts are represented by those features
                    filename = feature_file.split('/')[-1]
                    name = filename.split('.')[0]
                    frame_start = int(name.split('_')[-2])
                    frame_end = int(name.split('_')[-1])
                    names = name.split('_')
                    print 'processing feature file "' + filename + '"' 
                    
                    concepts = []
                    for i in range(2,len(names)-2):
                        concepts.append(names[i])
                    print 'concepts: ' + repr(concepts) 

                    features = []
                    file = open(feature_file,'r')
                    for line in file:
                        feature_vector = convert_to_numeric_vector(line.strip().split())
                        features.append(feature_vector)
                    file.close()
                    
                    print 'sorting feature vectors...'
                    features.sort(key=itemgetter(2))
                    
                    window_end = frame_start + tsz - 1
                    filename = 'data.txt'
                    file = open(filename, 'w')
                    for i in range(len(features)):
                        if features[i][2] <= window_end and i < len(features):
                            file.write(repr(features[i][0]))
                            for j in range(1,len(features[i])):
                                file.write(' ' + repr(features[i][j]))
                            file.write('\n')
                        else:
                            # close file and make it ready to be used for histogram building
                            if i == len(features) - 1:
                                file.write(repr(features[i][0]))
                                for j in range(1,len(features[i])):
                                    file.write(' ' + repr(features[i][j]))
                                file.write('\n')    
                            file.close()
                            
                            # update the temporal window location
                            window_end += tsz
                        
                            # setting processing params
                            hof_start = 75
                            hof_dimension = 90
                            output_filename = fold_path + '/' + concepts[0] + '.hist'
                            
                            cmd_options = '--build_histograms '
                            cmd_options += ' --codebook_path ' + codebook_path + '/actions'
                            cmd_options += ' --dimension ' + str(hof_dimension)
                            cmd_options += ' --start ' + str(hof_start)
                            cmd_options += ' --input_file ' + filename
                            cmd_options += ' --output_file ' + output_filename
                            if libsvm == True:
                                cmd_options += ' --libsvm ' + str(class_label)
                            
                            # execute program to compute histograms    
                            print 'Executing ' + program_path + ' ' + cmd_options 
                            os.system(program_path + ' ' + cmd_options)

                            for j in range(1,len(concepts)):
                                # feature parse param setting
                                hog_start = 3
                                hog_dimension = 72
                                
                                # construct output filename
                                output_filename = fold_path + '/' + concepts[j] + '.hist'
                                
                                # setting command options of the program
                                cmd_options = '--build_histograms '
                                cmd_options += ' --codebook_path ' + codebook_path + '/objects'
                                cmd_options += ' --dimension ' + str(hog_dimension)
                                cmd_options += ' --start ' + str(hog_start)
                                cmd_options += ' --input_file ' + filename
                                cmd_options += ' --output_file ' + output_filename
                                if libsvm == True:
                                    cmd_options += ' --libsvm ' + str(class_label)
                                
                                # execute program to assemble histograms  
                                print 'Executing ' + program_path + ' ' + cmd_options  
                                os.system(program_path + ' ' + cmd_options)
                                
                            # open empty file to store data of the next temporal window and construct the next histogram
                            file = open(filename, 'w')
                            file.write(repr(features[i][0]))
                            for j in range(1,len(features[i])):
                                file.write(' ' + repr(features[i][j]))
                            file.write('\n')      
                    file.close()     
                    del features[:]
                    # for each action and object
                    #for concept_file in glob.glob(concept_path + '/*'):
                    #output_concept_filename = fold_path + '/codebook/' + name + '/' + concept_file.split('/')[-1] 
                    #print output_concept_filename
                    #concat_files([concept_file],output_concept_filename)
        #del features[:]
        #print "where features deleted? " + repr(features)

def build_codebooks(root_path='../experiments', program_path='./GMMBoVW'):
    # setting command options of the program
    hog_start = 3
    hog_dimension = 72
    hof_start = 75
    hof_dimension = 90
    actions_codebook_size = 400
    objects_codebook_size = 600
    
    for fold_path in glob.glob(root_path + '/*'):
        data_file = fold_path + '/codebook/actions/actions.hof'
        for file in glob.glob(fold_path + '/codebook/actions/*.hofhog'):
            concat_files([file],data_file)
        
        cmd_options = '--build_codebook ' + fold_path + '/codebook/actions'
        cmd_options += ' --codebook_size ' + str(actions_codebook_size)
        cmd_options += ' --dimension ' + str(hof_dimension)
        cmd_options += ' --start ' + str(hof_start)
        cmd_options += ' --input_file ' + data_file
        
        # execute program to assemble histograms    
        print program_path + ' ' + cmd_options
        os.system(program_path + ' ' + cmd_options)
        
        data_file = fold_path + '/codebook/objects/objects.hog'
        for file in glob.glob(fold_path + '/codebook/objects/*.hofhog'):
            concat_files([file],data_file)
            
        cmd_options = '--build_codebook ' + fold_path + '/codebook/objects'
        cmd_options += ' --codebook_size ' + str(objects_codebook_size)
        cmd_options += ' --dimension ' + str(hog_dimension)
        cmd_options += ' --start ' + str(hog_start)
        cmd_options += ' --input_file ' + data_file  
        
        # execute program to assemble histograms
        print program_path + ' ' + cmd_options    
        os.system(program_path + ' ' + cmd_options)     


def prepare_unit_features_for_histogram(annotation_filename='P03/P03_cereal.coarse',
                                        feature_filename='P03_cereals_stipdet.txt',
                                        output_path='.', extract_features=False, delimiters=['_','2'],
                                        label_ignore_list=['SIL']):
    feature_handler = FeatureHandler()
    annt_file = open(annotation_filename,'r')
    subject = feature_filename.split('/')[-3]
    cam = feature_filename.split('/')[-2]
    activity = feature_filename.split('/')[-1].split('_')[1]
    if activity == 'cereals': activity = 'cereals'
    if activity == 'salat': activity = 'salad'
    sampling_rate = 1.

    for line in annt_file:
        # parse annotation file line
        data = line.strip().split()
        frame_range = string.split(data[0],'-')
        regex_pattern = '|'.join(map(re.escape, delimiters))
        concepts = re.split(regex_pattern, data[1])

        print repr(concepts)

        concept_name = subject + '_' + activity + '_' + cam
        for i in range(len(concepts)):
            concept_name += '_' + concepts[i]
        concept_name += '_' + frame_range[0] + '_' + frame_range[1]

        feature_handler.parse_features(feature_filename, output_path + '/' + concept_name + '.hofhog', 'w',
                                       ['hog','hof'], [], [], [int(frame_range[0]), int(frame_range[1])], sampling_rate)


def main():

    # prepare test features for unit recognition performance
    k = 4
    code = [0, 16, 29, 42, 53]
    output_path = 'unit_test_features'

    annotation_file_list = []
    recursive_file_search(['../Breakfast_Final/lab_raw'], annotation_file_list, ['coarse'])

    feature_file_list = []
    recursive_file_search(['../BreakfastII_15fps_qvga_sync'], feature_file_list, ['_stipdet.txt'])

    if os.path.isdir(output_path) == False:
        os.system('mkdir ' + output_path)
    if os.path.isdir(output_path + '/s' + str(k)) == False:
        os.system('mkdir ' + output_path + '/s' + str(k))
    output_path += '/s' + str(k)

    for annt_file in annotation_file_list:
        
        subject_id = int(annt_file.split('/')[-1].split('_')[0].split('P')[-1])
        if subject_id < code[k-1] or subject_id >= code[k]: continue

        print annt_file
        activity = annt_file.split('/')[-1].split('.')[0].split('_')[1]
        #print activity
        for feature_file in feature_file_list:

            filename = feature_file.split('/')[-1]

            # check if same activity
            activity2 = filename.split('.')[0].split('_')[1]

            if activity2 == 'cereals': activity2 = 'cereal'
            if activity2 == 'salat': activity2 = 'salad'

            print activity,'==',activity2,'?'
            if activity != activity2: continue

            # check if same id
            subject = filename.split('_')[0]
            id = int(subject.split('P')[1])
            print id
            if id != subject_id: continue

            print feature_file

            # extract features
            prepare_unit_features_for_histogram(annt_file, feature_file, output_path)

    #prepare_test_features(4,'../BreakfastII_15fps_qvga_sync','../test_features')

    #construct_training_histograms()

    #build_codebooks()

    #output_path = '/Volumes/FDMS_PHD_1/experiments'
    #training_path = '/Volumes/FDMS_PHD_1/codebook_features'
    #prepare_fold_codebook_features(training_path, output_path)     
    
if __name__ == "__main__":
    main()

