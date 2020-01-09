#!/usr/bin/python

import os
import sys
import glob
import string
import re

from FeatureHandler import *

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

def read_training_folders(root_path='breakfast',file_extensions=['coarse']):
    file_list = []
    recursive_file_search([root_path],file_list,file_extensions)
    return file_list
    
# find generators and their bond structures using annotation files
def construct_ontological_constraints(annotation_filename, modalities, action_dic=None, object_dic=None, interactions=None, recipes=None, delimiters=['_','2'], label_ignore_list=['SIL']):
    
    if action_dic == None:
        action_dic = {}
    if object_dic == None:
        object_dic = {}
    if interactions == None:
        interactions = []
    if recipes == None:
        recipes = []
    
    butter_counter = 0
    
    generator_list = []
    action_bond_structure = {}
    object_bond_structure = {}
    
    recipe_name = annotation_filename.split('/')[-1].split('_')[1].split('.')[0] + '_recipe'
    recipes.append(recipe_name)
    recipes = list(set(recipes))
    
    annt_file = open(annotation_filename,'r')    
    for line in annt_file:
        print line
    
        # parse file line
        data = line.strip().split()
        frame_range = string.split(data[0],'-')
        regex_pattern = '|'.join(map(re.escape, delimiters))
        concepts = re.split(regex_pattern, data[1])
        
        # first word is a verb and rest will typically be objects
        if concepts[0] not in label_ignore_list:
            if len(concepts) > 1:
                # for action names that are phrasal verbs
                if concepts[1] in ['in','out','on','up']:
                    # concept_name = subject + '_' + cam + '_' + concepts[0] + '_' + concepts[1]
                    concept_name = concepts[0] + '_' + concepts[1]
                    action_name = concept_name
                    if concept_name not in action_dic:
                        action_dic[action_name] = []
                    
                    prev_object = ' '
                    for i in range(2,len(concepts)):
                        #concept_name = subject + '_' + cam + '_' + concepts[i]
                        concept_name = concepts[i]
                        if concept_name not in object_dic:
                            object_dic[concept_name] = []
                            
                        if i == 2:
                            prev_object = concept_name
                        else:
                            object_dic[concept_name].append(prev_object)
                        action_dic[action_name].append(concept_name)
                        
                        print action_name + '-->' + concept_name
                        interactions.append(action_name+'_'+concept_name)
                        #interactions = list(set(interactions))
                        
                else:
                    action_name = ' '
                    prev_object = ' '
                    count_objects = 0
                    for i in range(len(concepts)):
                        if i == 0:
                            action_name = concepts[i]
                            if action_name not in action_dic:
                                action_dic[action_name] = []
                        else:
                            concept_name = concepts[i]
                            action_dic[action_name].append(concept_name)
                            if concept_name not in object_dic:
                                object_dic[concept_name] = []
                            
                            if i == 1:
                                prev_object = concept_name
                            else:
                                object_dic[concept_name].append(prev_object)
                                print concept_name + '-->' + prev_object
                                interactions.append(prev_object+'_'+concept_name)
                                #interactions = list(set(interactions))
                                
                            action_dic[action_name].append(concept_name)
                            print action_name + '-->' + concept_name
                            interactions.append(action_name+'_'+concept_name)
                            #interactions = list(set(interactions))
                            
        
    annt_file.close()
    
    interactions = list(set(interactions))
    
    for action in action_dic:
        action_dic[action] = list(set(action_dic[action]))
        
    for object in object_dic:
        object_dic[object] = list(set(object_dic[object]))
    
    return (action_dic, object_dic, interactions, recipes)
      

def prepare_feature_for_histogram(annotation_filename='P03/P03_cereal.coarse', feature_filename='P03_cereals_stipdet.txt', output_path='.', extract_features=False, delimiters=['_','2'], label_ignore_list=['SIL']):
    feature_handler = FeatureHandler()
    annt_file = open(annotation_filename,'r')
    subject = feature_filename.split('/')[-3]
    cam = feature_filename.split('/')[-2]
    sampling_rate = 1.
    
    for line in annt_file:
        # parse annotation file line
        data = line.strip().split()
        frame_range = string.split(data[0],'-')
        regex_pattern = '|'.join(map(re.escape, delimiters))
        concepts = re.split(regex_pattern, data[1])

        print repr(concepts)
        
        concept_name = subject + '_' + cam
        for i in range(len(concepts)):
            concept_name += '_' + concepts[i]
        concept_name += '_' + frame_range[0] + '_' + frame_range[1]
        
        feature_handler.parse_features(feature_filename, output_path + '/' + concept_name + '.hofhog', 'a', ['hog','hof'], [],[],[int(frame_range[0]), int(frame_range[1])], sampling_rate) 
        
def read_training_points(annotation_filename='P03/P03_cereal.coarse', feature_filename='P03_cereals_stipdet.txt', output_path='.', extract_features=False, delimiters=['_','2'], label_ignore_list=['SIL']):
    feature_handler = FeatureHandler()
    annt_file = open(annotation_filename,'r')
    subject = feature_filename.split('/')[-3]
    cam = feature_filename.split('/')[-2]
    sampling_rate = 0.05
    
    if os.path.isdir(output_path + '/actions') == False:
        os.system('mkdir ' + output_path + '/actions')
        
    if os.path.isdir(output_path + '/objects') == False:
        os.system('mkdir ' + output_path + '/objects')
    
    for line in annt_file:
        
        # parse annotation file line
        data = line.strip().split()
        frame_range = string.split(data[0],'-')
        regex_pattern = '|'.join(map(re.escape, delimiters))
        concepts = re.split(regex_pattern, data[1])
#        concepts = string.split(data[1],delimiters)
        
        print repr(concepts)
        
        # first word is a verb and rest will typically be objects
        if concepts[0] not in label_ignore_list:
            if len(concepts) > 1:
                # for action names that are phrasal verbs
                if concepts[1] in ['in','out','on','up']:
                    #concept_name = subject + '_' + cam + '_' + concepts[0] + '_' + concepts[1]
                    concept_name = concepts[0] + '_' + concepts[1]
                    print concept_name
                    feature_handler.parse_features(feature_filename, output_path + '/actions/' + concept_name + '.hofhog', 'a', ['hog','hof'], [],[],[int(frame_range[0]), int(frame_range[1])], sampling_rate)
                    # objects if any...
                    for i in range(2,len(concepts)):
                        #concept_name = subject + '_' + cam + '_' + concepts[i]
                        concept_name = concepts[i]
                        print concept_name
                        feature_handler.parse_features(feature_filename, output_path + '/objects/' + concept_name + '.hofhog', 'a', ['hog','hof'], [],[],[int(frame_range[0]), int(frame_range[1])], sampling_rate)  
                else:
                    for i in range(len(concepts)):
                        #concept_name = subject + '_' + cam + '_' + concepts[i]
                        concept_name = concepts[i]
                        if i == 0:
                            output_dir = output_path + '/actions'
                        else:
                            output_dir = output_path + '/objects'
                        print concept_name
                        feature_handler.parse_features(feature_filename, output_dir + '/' + concept_name + '.hofhog', 'a', ['hog','hof'], [],[],[int(frame_range[0]), int(frame_range[1])], sampling_rate)




def construct_time_cooccurrence_tables():
    pass
 
def construct_simple_cooccurrence_tables(table,annotation_file_list,time=False,delimiters=['_','2']):
    # as interactions are found, increment 1     
    for file_path in annotation_file_list:
        filename = file_path.split('/')[-1]
        recipe_name = filename.split('_')[1].split('.')[0]
        print recipe_name
        
        #if recipe_name+'_recipe' not in generators_bond_structure:
        #    generators_bond_structure[recipe_name+'_recipe'] = []
        
        past_interactions = []
        curr_interactions = []
        file = open(file_path,'r')
        for line in file:
            # parse file line
            data = line.strip().split()
            frame_range = string.split(data[0],'-')
            regex_pattern = '|'.join(map(re.escape, delimiters))
            concepts = re.split(regex_pattern, data[1])
            
            # skip SIL (they are unimportant for the matter)
            if len(concepts) > 1 :
                start = 1
                action_name = concepts[0]
                if concepts[start] in ['in','out','on','up']:
                    action_name += '_' + concepts[start]
                    start += 1
                
                #if action_name not in generators_bond_structure:
                #    generators_bond_structure[action_name] = ['hof','time','recipe']
                
                # find the pairwise connections between action and objects, etc.
                curr_object_name = ''    
                for i in range(start,len(concepts)):
                    object_name = concepts[i] 
                    interaction_name = action_name + '_' + object_name
                    if time == False:
                        if action_name in table:
                            if object_name in table[action_name]:
                                table[action_name][object_name] += 1
                        elif curr_object_name in table:
                            if object_name in table[curr_object_name]:
                                table[curr_object_name][object_name] += 1
                        elif interaction_name in table:
                            if recipe_name+'_recipe' in table[interaction_name]: 
                                table[interaction_name][recipe_name+'_recipe'] += 1
                            elif action_name in table[interaction_name]:
                                table[interaction_name][action_name] += 1
                            elif object_name in table[interaction_name]:
                                table[interaction_name][object_name] += 1
                    else:
                        curr_interactions.append(interaction_name)
                        if len(past_interactions) > 0:
                            for inter in past_interactions:
                                if inter in table:
                                    if object_name in table[inter]:
                                        table[inter][object_name] += 1
                if time == True:                    
                    for inter in past_interactions:
                        if inter in table:
                            if action_name in table[inter]:
                                table[inter][action_name] += 1
                    
                del past_interactions[:]
                past_interactions = curr_interactions
                curr_interactions = []
                            
                    #for key in modalities:
                    #    if object_name in modalities[key]:
                    #        generators_bond_structure[action_name].append(key)
                    #        generators_bond_structure[action_name] = list(set(generators_bond_structure[action_name]))
                    #        break
                            
                    #if object_name not in generators_bond_structure:
                    #    generators_bond_structure[object_name] = ['hog','time','recipe']
                    
                    #if prev_object_name != '':
                    #    for key in modalities:
                    #        if prev_object_name in modalities[key]:
                    #            generators_bond_structure[object_name].append(key) 
                    #            generators_bond_structure[object_name] = list(set(generators_bond_structure[object_name]))     
                    #            break  
                        
        file.close()
        
    #print 'bond structure: '  
    #for generator in generators_bond_structure:
    #    print generator + ': ' + repr(generators_bond_structure[generator])
    
    print_table(table)
    
    return table
    

def random_select_items(point_list=[], percentage=0.5):
    number_of_points = len(point_list)
    number_of_samples = int(percentage * number_of_points)
    number_of_samples = number_of_points if number_of_samples > number_of_points else number_of_samples
    sampled_points = random.sample(point_list, number_of_samples)
    return sampled_points


def create_bond_structure(annotation_file_list,modalities,delimiters=['_','2']):
    generators_bond_structure = {}
    for file_path in annotation_file_list:
        filename = file_path.split('/')[-1]
        recipe_name = filename.split('_')[1].split('.')[0]
        print recipe_name
        
        if recipe_name+'_recipe' not in generators_bond_structure:
            generators_bond_structure[recipe_name+'_recipe'] = []
        
        file = open(file_path,'r')
        for line in file:
            # parse file line
            data = line.strip().split()
            frame_range = string.split(data[0],'-')
            regex_pattern = '|'.join(map(re.escape, delimiters))
            concepts = re.split(regex_pattern, data[1])
            
            # skip SIL (they are unimportant for the matter)
            if len(concepts) > 1 :
                start = 1
                action_name = concepts[0]
                if concepts[start] in ['in','out','on','up']:
                    action_name += '_' + concepts[start]
                    start += 1
                
                if action_name not in generators_bond_structure:
                    generators_bond_structure[action_name] = ['hof-svm','hof-gmm','action','recipe']
                
                prev_object_name = ''    
                for i in range(start,len(concepts)):
                    object_name = concepts[i] 
                    for key in modalities:
                        if object_name in modalities[key]:
                            generators_bond_structure[action_name].append(key)
                            generators_bond_structure[action_name] = list(set(generators_bond_structure[action_name]))
                            break
                            
                    if object_name not in generators_bond_structure:
                        generators_bond_structure[object_name] = ['hog-svm','hog-gmm','object','recipe']
                    
                    if prev_object_name != '':
                        for key in modalities:
                            if prev_object_name in modalities[key]:
                                generators_bond_structure[object_name].append(key) 
                                generators_bond_structure[object_name] = list(set(generators_bond_structure[object_name]))     
                                break  
                        
        file.close()
        
    print 'bond structure: '  
    for generator in generators_bond_structure:
        print generator + ': ' + repr(generators_bond_structure[generator])
        
    return generators_bond_structure
    
def prepare_table(row,col):
    table = {}
    for i in row:
        table[i] = {}
        for j in col:
            table[i][j] = 0
            
    return table

def save_bond_structure_on_file(bond_structures,levels,modalities,filename):
    level = ''
    file = open(filename,'w')
    for generator in bond_structures:
        for m in modalities:
            if generator in modalities[m]:
                level = str(levels[m])
                break
        file.write(generator + ' ' + level)
        if len(bond_structures[generator])>0:
            file.write(' ' + bond_structures[generator][0])             
        for i in range(1,len(bond_structures[generator])):
            file.write(',' + bond_structures[generator][i])
        file.write('\n')
    file.close()

def save_table_on_file(table,filename):
    file = open(filename,'w')
    for i in table:
        file.write(i+',')
        for j in table[i]:
            file.write(j+':'+repr(table[i][j]))
        file.write('\n')
    file.close()
    
def print_table(table):
    for i in table:
        for j in table[i]:
            print '[' + i + ']' + '[' + j + '] = ' + repr(table[i][j]) + ' '
        print '\n'

def filter_annotation_files(annotation_file_list, split_number):
    filtered_annotation_files = []
    for annotation_file in annotation_file_list:
        annt_filename = annotation_file.split('/')[-1]
        subject_id = annt_filename.split('_')[0]
        activity_name = annt_filename.split('_')[1][0:3] # this is a hack...

#        print 'annt: ' + annotation_file +' subject id: ' + subject_id.split('P')[1]

        sid = int(subject_id.split('P')[1])
        if split_number == 1:
            if sid >= 16:
                filtered_annotation_files.append(annotation_file)
        elif split_number == 2: 
            if sid < 16 or sid >= 29:
                filtered_annotation_files.append(annotation_file) 
        elif split_number == 3: 
            if sid < 29 or sid >= 42:
                filtered_annotation_files.append(annotation_file)
        elif split_number == 4:
            if sid < 42:
                filtered_annotation_files.append(annotation_file)

    return filtered_annotation_files

def main():    
    split_number = int(sys.argv[1]) # ./train_prior_parameters.py 1 0.5 --> split s1 and 0.5 of the training set
    percentage = float(sys.argv[2])

    #print 'split number', split_number, 'percentage', percentage
    #exit(1)

    #training_file_path='/Volumes/FDMS_PHD_1/Breakfast_Final'
    training_file_path='../Breakfast_Final'
    root_path_lenth = len(training_file_path.split('/'))
    annotation_file_extensions=['coarse']
    annotation_file_list = read_training_folders(training_file_path,annotation_file_extensions)
 
    filtered_training_list = filter_annotation_files(annotation_file_list, split_number)
    sampled_training_list = random_select_items(filtered_training_list, percentage)
    print 'annotation_file_list', len(annotation_file_list), 'filtered_training_list size: ', len(filtered_training_list), 'sampled_training_list size: ', len(sampled_training_list) 

    levels = {'action': 3, 'object': 2, 'recipe': 4, 'hof-svm': 1, 'hof-gmm': 1, 'hog-svm': 1, 'hog-gmm': 1}
    modalities = { 'ingredient': ['cereals','tea','toppping','juice','dough','powder','milk','teabag', 
                   'sugar', 'orange', 'coffee', 'oil', 'flour', 'egg', 'water', 'glass', 'fruit', 'bun', 
                   'pancake', 'butter', 'toppingOnTop', 'saltnpepper', 'bunTogether'], 
                   'utensil': ['cup','bowl','pan','plate','squeezer', 'knife'],
                   'hof-svm': ['hof-svm'],
                   'hof-gmm': ['hof-gmm'],
                   'hog-gmm': ['hog-gmm'],
                   'hog-svm': ['hog-svm'], }
    
    action_dic = {}
    object_dic = {}
    interactions = []
    recipes = []
    for annotation_file in annotation_file_list:
        action_dic, object_dic, interactions, recipes = construct_ontological_constraints(annotation_file, modalities, action_dic, object_dic, interactions, recipes)
    
    print '\n\n********* ACTIONS AND OBJECTS **********\n\n'
    
    actions = []    
    for action in action_dic:
        actions.append(action)
        print action + ': ' + repr(action_dic[action])
    objects = []    
    for object in object_dic:
        objects.append(object)
        print object + ': ' + repr(object_dic[object])
    
    modalities['action'] = actions
    modalities['object'] = objects
    modalities['recipe'] = recipes    
    
    print '\n\n********* Bond Structures **********\n\n'
    
    # adding action and object generators with their bond structures
    bond_structures = create_bond_structure(sampled_training_list, modalities)
    
    # adding feature generators with their bond structures
    bond_structures['hof-svm'] = []
    bond_structures['hof-gmm'] = []
    bond_structures['hog-svm'] = []
    bond_structures['hog-gmm'] = [] 
    
    # adding recipe generators with their bond structures
    for recipe in recipes:
        bond_structures[recipe] = []
        
    save_bond_structure_on_file(bond_structures,levels,modalities,'breakfast_generator_space_s'+str(split_number)+'_'+str(percentage)+'.txt')
    
    # construct action x object table
    print 'generate obj obj table'
    table = prepare_table(objects,objects)               
    table = construct_simple_cooccurrence_tables(table,sampled_training_list)
    print repr(table)
    print_table(table)
    save_table_on_file(table,'breakfast_obj-obj_s'+str(split_number)+'_'+str(percentage)+'.txt')    
    
    print 'generate act obj table'
    table = prepare_table(actions,objects)
    table = construct_simple_cooccurrence_tables(table,sampled_training_list)
    save_table_on_file(table,'breakfast_obj-act_s'+str(split_number)+'_'+str(percentage)+'.txt')
    
    #print 'generate interactions obj table'
    #table = prepare_table(interactions,objects)               
    #table = construct_simple_cooccurrence_tables(table,sampled_training_list,True)
    #save_table_on_file(table,'breakfast_inter-obj.txt')
    
    #print 'generate interactions actions table'    
    #table = prepare_table(interactions,actions)               
    #table = construct_simple_cooccurrence_tables(table,sampled_training_list,True)
    #save_table_on_file(table,'breakfast_inter-act.txt')    
    
    #print 'generate interactions recipes table'
    #table = prepare_table(interactions,recipes)               
    #table = construct_simple_cooccurrence_tables(table,sampled_training_list)
    #save_table_on_file(table,'breakfast_inter-rec.txt')  
    
if __name__ == '__main__':
    main()
