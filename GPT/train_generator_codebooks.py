#!/usr/bin/python

import os
import glob
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
    

def construct_training_histograms(training_path, output_path, codebook_path, program_path='./GMMBoVW', libsvm=False, class_label=0, temporal_window_size=5):
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
                    
                    concepts = []
                    for i in range(2,len(name)-2):
                        concepts.append(name[i])
                    
                    file = open(filename,'r')
                    for line in file:
                        feature_vector = convert_to_numeric_vector(line.strip().split())
                        features.append(feature_vector)
                    file.close()
                    
                    features.sort(key=itemgetter(2))
                    
                    window_end = frame_start + tsz - 1
                    filename = 'data.txt'
                    file = open(filename, 'w')
                    for i in range(len(features)):
                        if features[i][2] <= window_end and i < len(features):
                            file.write(features[i][0])
                            for j in range(1,len(features[i])):
                                file.write(' ' + features[i][j])
                            file.write('\n')
                        else:
                            # close file and make it ready to be used for histogram building
                            if i == len(features) - 1:
                                file.write(features[i][0])
                                for j in range(1,len(features[i])):
                                    file.write(' ' + features[i][j])
                                file.write('\n')    
                            file.close()
                            
                            # update the temporal window location
                            window_end += tsz
                        
                            # setting processing params
                            hof_start = 75
                            hof_dimension = 90
                            output_filename = fold_path + '/' + concepts[0] + '.hist'
                            
                            cmd_options = '--build_histograms '
                            cmd_options += ' --codebook_path ' + codebook_path
                            cmd_options += ' --dimension ' + str(hog_dimension)
                            cmd_options += ' --start ' + str(hog_start)
                            cmd_options += ' --input_file ' + filename
                            cmd_options += ' --output_file ' + output_filename
                            if libsvm == True:
                                cmd_options += ' --libsvm ' + str(class_label)
                            
                            # execute program to compute histograms    
                            os.system(program_path + ' ' + cmd_options)

                            for j in range(1,len(concepts)):
                                # feature parse param setting
                                hog_start = 3
                                hog_dimension = 72
                                
                                # construct output filename
                                output_filename = fold_path + '/' + concepts[j] + '.hist'
                                
                                # setting command options of the program
                                cmd_options = '--build_histograms '
                                cmd_options += ' --codebook_path ' + codebook_path
                                cmd_options += ' --dimension ' + str(hog_dimension)
                                cmd_options += ' --start ' + str(hog_start)
                                cmd_options += ' --input_file ' + filename
                                cmd_options += ' --output_file ' + output_filename
                                if libsvm == True:
                                    cmd_options += ' --libsvm ' + str(class_label)
                                
                                # execute program to assemble histograms    
                                os.system(program_path + ' ' + cmd_options)
                                
                            # open empty file to store data of the next temporal window and construct the next histogram
                            file = open(filename, 'w')
                            file.write(features[i][0])
                            for j in range(1,len(features[i])):
                                file.write(' ' + features[i][j])
                            file.write('\n')      
                    file.close()     
                    
                    # for each action and object
                    #for concept_file in glob.glob(concept_path + '/*'):
                    #output_concept_filename = fold_path + '/codebook/' + name + '/' + concept_file.split('/')[-1] 
                    #print output_concept_filename
                    #concat_files([concept_file],output_concept_filename)
        del features[:]
        print "where features deleted? " + repr(features)

def build_codebooks(root_path='/Volumes/FDMS_PHD_1/experiments', program_path='./GMMBoVW'):
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

def main():


    build_codebooks()

    #output_path = '/Volumes/FDMS_PHD_1/experiments'
    #training_path = '/Volumes/FDMS_PHD_1/codebook_features'
    #prepare_fold_codebook_features(training_path, output_path)     
    
if __name__ == "__main__":
    main()

