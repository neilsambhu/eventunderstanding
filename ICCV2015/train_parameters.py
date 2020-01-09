#!/usr/bin/python

import os
import sys
import glob
import string
import re

from FeatureHandler import *

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

def random_select_items(point_list=[], percentage=0.5):
    number_of_points = len(point_list)
    number_of_samples = int(percentage * number_of_points)
    number_of_samples = number_of_points if number_of_samples > number_of_points else number_of_samples
    sampled_points = random.sample(point_list, number_of_samples)
    return sampled_points

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


def parse_annotation_to_find_generators(annotation_file_list,delimiters=['_','2']):
    recipes = []
    interactions = []
    actions = []
    objects = []

    # as interactions are found, increment 1     
    for file_path in annotation_file_list:
        # get recipe's name
        filename = file_path.split('/')[-1]
        recipe_name = filename.split('_')[1].split('.')[0]
        print recipe_name

        # update list of recipes
        recipes.append(recipe_name+'-r')
        recipes = list(set(recipes))
        
        file = open(file_path,'r')
        for line in file:
            # parse file line
            data = line.strip().split()
            frame_range = string.split(data[0],'-')
            regex_pattern = '|'.join(map(re.escape, delimiters))
            concepts = re.split(regex_pattern, data[1])

            # skip SIL (they are unimportant for the matter)
            if len(concepts) > 1 :
                # construct action name
                start = 1
                action_name = concepts[0]
                if concepts[start] in ['in','out','on','up','down']:
                    action_name += concepts[start]
                    #action_name += '_' + concepts[start]
                    start += 1
                action_name += '-a'

                # update list of actions
                actions.append(action_name)
                actions = list(set(actions))

                # construct interaction name
                interaction_name = action_name
                for i in range(start,len(concepts)):
                    interaction_name += '_'+concepts[i]+'-o'
                    objects.append(concepts[i]+'-o')

                # update list of interactions
                interactions.append(interaction_name)
                interactions = list(set(interactions))

                # update list of objects
                objects = list(set(objects))
        file.close()

    return recipes,interactions,actions,objects

def construct_time_cooccurrence_tables():
    pass
 
def construct_simple_cooccurrence_tables(table,annotation_file_list,time=False,delimiters=['_','2']):
    # as interactions are found, increment 1     
    for file_path in annotation_file_list:
        filename = file_path.split('/')[-1]
        recipe_name = filename.split('_')[1].split('.')[0]
        recipe_name += '-r'
        print recipe_name
        
        #if recipe_name+'_recipe' not in generators_bond_structure:
        #    generators_bond_structure[recipe_name+'_recipe'] = []
        
        past_action_name = ''
        past_objects = []
        #past_interactions = []
        #curr_interactions = []
        file = open(file_path, 'r')
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
                if concepts[start] in ['in','out','on','up','down']:
                    action_name += concepts[start]
                    #action_name += '_' + concepts[start]
                    start += 1
                action_name += '-a'
               
                # construct interaction name
                interaction_name = action_name
                for i in range(start,len(concepts)):
                    interaction_name += '_'+concepts[i]+'-o'

                # count co-occurrence of interaction and recipe 
                if recipe_name in table:
                    if interaction_name in table[recipe_name]:
                        table[recipe_name][interaction_name] += 1.

                #if action_name not in generators_bond_structure:
                #    generators_bond_structure[action_name] = ['hof','time','recipe']                
                #past_object_name = ''
                #passive_object_name = ''  
                for i in range(start,len(concepts)):
                    object_name = concepts[i]+'-o'
                    #interaction_name = action_name + '_' + object_name
                    if time == False:
                        # to construct action-action table
                        if action_name in table:
                            if object_name in table[action_name]:
                                table[action_name][object_name] += 1.
                        # to construct object-object table
                        #elif object_name in table:
                        #    if passive_object_name in table[object_name]:
                        #        table[object_name][passive_object_name] += 1
                        # to construct interaction-action table or interaction-object table
                        elif interaction_name in table:
                            if action_name in table[interaction_name]:
                                table[interaction_name][action_name] += 1
                            elif object_name in table[interaction_name]:
                                table[interaction_name][object_name] += 1
                    else: # if dependent on time
                        # check if past_action-curr_action table
                        if past_action_name in table:
                            if action_name in table[past_action_name]:
                                table[past_action_name][action_name] += 1
                        # temporal co-occurrence of objects
                        else:
                            for past_object_name in past_objects : 
                                if past_object_name in table:
                                    if object_name in table[past_object_name]:
                                        table[past_object_name][object_name] += 1

                        #curr_interactions.append(interaction_name)
                        #if len(past_interactions) > 0:
                        #    for inter in past_interactions:
                        #        if inter in table:
                        #            if object_name in table[inter]:
                        #                table[inter][object_name] += 1
                  
                    #passive_object_name = object_name

                # object co-occurrence 
                list_of_objects = []
                for i in range(start, len(concepts)):
                    list_of_objects.append(concepts[i])

                # avoid to compute co-occurrence of same concepts
                list_of_objects = list(set(list_of_objects))

                # compute co-occurrence of objects (should be symmetric)
                for i in range(start, len(concepts)):
                    for j in range(start+1, len(concepts)):
                        if concepts[i]+'-o' in table and concepts[j]+'-o' in table[concepts[i]+'-o']:
                            table[concepts[i]+'-o'][concepts[j]+'-o'] += 1
                        if concepts[j]+'-o' in table and concepts[i]+'-o' in table[concepts[j]+'-o']:
                            table[concepts[j]+'-o'][concepts[i]+'-o'] += 1

                # update list of past objects
                del past_objects[:]
                for i in range(start,len(concepts)):
                    past_objects.append(concepts[i]+'-o')

                # for past interactions to next action
                #if time == True:
                #    for inter in past_interactions:
                #        if inter in table:
                #            if action_name in table[inter]:
                #                table[inter][action_name] += 1

                # udpate past action
                past_action_name = action_name
        file.close()
    print_table(table)
    
    return table
    
class Bond:
    def __init__(self, value, marker, type):
        self.value = value   # modalities such as 'action', 'object'
        self.marker = marker # 'in' for in-bond or 'out' for out-bond
        self.type = type     # type: 'temporal', 'semantic', 'support'

def generator_exists():
    pass

def find_bond_structures(annotation_file_list,modalities,delimiters=['_','2']):
    generator_names = {}
    generators_bond_structure = {}

    actions_bond_structures = {}
    objects_bond_structures = {}
    interactions_bond_structures = {}
    recipes_bond_structures = {}

    new_recipe_generators = {}
    new_interaction_generators = {}
    new_action_generators = {}
    new_object_generators = {}

    for file_path in annotation_file_list:
        filename = file_path.split('/')[-1]
        recipe_name = filename.split('_')[1].split('.')[0]
        recipe_name += '-r'
        new_recipe_generators[recipe_name] = []
        print recipe_name

        #new_generators.append([recipe_name])

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
                if concepts[start] in ['in','out','on','up','down','into','upon']:
                    action_name += concepts[start]
                    #action_name += '_'+concepts[start]
                    start += 1
                action_name += '-a'

                # create interaction generator's bond structure
                interaction_name = action_name
                for i in range(start,len(concepts)):
                    interaction_name += '_'+concepts[i]+'-o'

                #interaction_name = '_'.join(concepts)
                new_interaction_generators[interaction_name] = [ interaction_name+':in:semantic', action_name + ':out:semantic' ]
                for i in range(start,len(concepts)):
                    object_name = concepts[i]+'-o'
                    new_interaction_generators[interaction_name].append( object_name+':out:semantic' )

                # create recipe generator's bond structure
                new_recipe_generators[recipe_name].append( interaction_name+':out:semantic' )

                # create action generator's bond structure
                new_action_generators[action_name] = [ action_name+':in:semantic', 'action:out:temporal' ]

                prev_object_name = ''
                for i in range(start,len(concepts)):
                    object_name = concepts[i]
                    if object_name not in new_object_generators:
                        new_object_generators[object_name] = []
                    # update action generator's bond structure with out-bonds to connect with objects
                    #object_name = concepts[i]
                    for key in modalities:
                        if object_name in modalities[key]:
                            # use the modality of the object 'object_name' as the generator
                            new_action_generators[action_name].append( key+':out:semantic' )
                            # get rid of repetitions
                            #new_action_generator[action_name] = list(set(generators_bond_structure[action_name]))
                            break

                    # create bond structure of generator 
                    #if object_name not in generators_bond_structure:
                    # use the modality of the object
                    new_object_generators[object_name] = [ object_name+':in:semantic', 'object:out:temporal' ]

                    # if it is the second object
                    if prev_object_name != '':
                        # find the modality of the contained object
                        for key in modalities:
                            if prev_object_name in modalities[key]:
                                # use modality of previous object as bond value of out-bond in the 'object_name' generator
                                new_object_generators[object_name].append( key+':out:semantic' )
                                # get rid of repetitions
                                #new_object_generators[object_name] = list(set(generators_bond_structure[object_name]))
                                break
                    prev_object_name = object_name

                # discard replicates
                for object_name in new_object_generators:
                    if not generator_exists(object_name,new_object_generators,objects_bond_structures):
                        if object_name not in objects_bond_structures:
                            objects_bond_structures[object_name] = [ ]
                        objects_bond_structures[object_name].append(new_object_generators[object_name])
                del new_object_generators
                new_object_generators = {}

                if not generator_exists(action_name,new_action_generators,actions_bond_structures):
                    if action_name not in actions_bond_structures:
                        actions_bond_structures[action_name] = [ ]
                    actions_bond_structures[action_name].append(new_action_generators[action_name])
                del new_action_generators
                new_action_generators = {}

                if not generator_exists(interaction_name,new_interaction_generators,interactions_bond_structures):
                    if interaction_name not in interactions_bond_structures:
                        interactions_bond_structures[interaction_name] = [ ]
                    interactions_bond_structures[interaction_name].append(new_interaction_generators[interaction_name])
                del new_interaction_generators
                new_interaction_generators = {}
        file.close()

        if not generator_exists(recipe_name,new_recipe_generators,recipes_bond_structures):
            if recipe_name not in recipes_bond_structures:
               recipes_bond_structures[recipe_name] = [ ]
            recipes_bond_structures[recipe_name].append(new_recipe_generators[recipe_name])
        del new_recipe_generators
        new_recipe_generators = {}


        # check if parsed generators already exist with the parsed bond structure
        

    print 'bond structure: '
    for generator in recipes_bond_structures:
        print generator + ': ' + repr(recipes_bond_structures[generator])

    for generator in interactions_bond_structures:
        print generator + ': ' + repr(interactions_bond_structures[generator])

    for generator in actions_bond_structures:
        print generator + ': ' + repr(actions_bond_structures[generator])

    for generator in objects_bond_structures:
        print generator + ': ' + repr(objects_bond_structures[generator])

    

def generator_exists(gname,new_generators,generators):
    #for gname in new_generators:
    if gname in generators:
        new_bond_structure = new_generators[gname]
        m = len(new_bond_structure)
        for bond_structure in generators[gname]:
            n = len(bond_structure)           
            if m == n:
                bond_value_counter = [ value for value in new_bond_structure ]
                for val in bond_structure:
                    if val in bond_value_counter:
                        bond_value_counter.remove(val)
                if not bond_value_counter:
                    return True
    #else:
    #    generators[new_generators[gname]
    return False

def create_bond_structure(annotation_file_list, modalities, delimiters=['_','2']):
    generator_names = {}
    generators_bond_structure = {}
    for file_path in annotation_file_list:
        filename = file_path.split('/')[-1]
        recipe_name = filename.split('_')[1].split('.')[0]
        recipe_name += '-r'
        print recipe_name
        
        if recipe_name not in generators_bond_structure:
            generators_bond_structure[recipe_name] = []
        
        file = open(file_path, 'r')
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
                if concepts[start] in ['in','out','on','up','down','into','upon']:
                    action_name += concepts[start]
                    #action_name += '_' + concepts[start]
                    start += 1
                action_name += '-a'

                # create interaction generator's bond structure
                #interaction_name = '_'.join(concepts)
                interaction_name = action_name
                for i in range(start,len(concepts)):
                    interaction_name += '_' + concepts[i] + '-o'

                if interaction_name not in generators_bond_structure:
                    generators_bond_structure[interaction_name] = [ interaction_name + ':in:semantic', action_name + ':out:semantic' ]
                    for i in range(start,len(concepts)):
                        object_name = concepts[i] + '-o'
                        generators_bond_structure[interaction_name].append(object_name+':out:semantic')

                # create recipe generator's bond structure
                generators_bond_structure[recipe_name].append(interaction_name+':out:semantic')
                generators_bond_structure[recipe_name] = list(set(generators_bond_structure[recipe_name]))

                # create action generator's bond structure
                if action_name not in generators_bond_structure:
                    generators_bond_structure[action_name] = [ action_name+':in:semantic', 'action:out:temporal' ]
                
                # 
                prev_object_name = ''
                for i in range(start,len(concepts)):
                    # update action generator's bond structure with out-bonds to connect with objects
                    object_name = concepts[i]+'-o'
                    for key in modalities:
                        if object_name in modalities[key]:
                            # use the modality of the object 'object_name' as the generator
                            generators_bond_structure[action_name].append( key+':out:semantic' )
                            # get rid of repetitions
                            generators_bond_structure[action_name] = list(set(generators_bond_structure[action_name]))
                            break

                    # create bond structure of generator 
                    if object_name not in generators_bond_structure:
                        # use the modality of the object
                        generators_bond_structure[object_name] = [ object_name+':in:semantic', 'object:out:temporal' ]
                    
                    # if it is the second object
                    if prev_object_name != '':
                        # find the modality of the contained object
                        for key in modalities:
                            if prev_object_name in modalities[key]:
                                # use modality of previous object as bond value of out-bond in the 'object_name' generator
                                generators_bond_structure[object_name].append( key+':out:semantic' )
                                # get rid of repetitions
                                generators_bond_structure[object_name] = list(set(generators_bond_structure[object_name]))     
                                break
                    prev_object_name = object_name    
        file.close()
        
    print 'bond structure: '  
    for generator in generators_bond_structure:
        print generator + ': ' + repr(generators_bond_structure[generator])
        
    return generators_bond_structure
    
def prepare_table(row, col):
    table = {}
    for i in row:
        table[i] = {}
        for j in col:
            table[i][j] = 0
    return table

def find_generator_level(generator, modalities, levels):
    level = -1
    for m in modalities:
        if generator in modalities[m]:
            level = levels[m]
            break
    # level=4 represents interactions
    level = level if level > 0 else 4
    return level

def save_bond_structure_on_file(bond_structures, levels, modalities, filename):
    # assemble generator space
    generator_space = []
    for generator in bond_structures:
        # discover generator's level (POSET connectors)
        level = find_generator_level(generator, modalities, levels)
        generator_space.append((generator, level, bond_structures[generator]))

    # sort generators in place according to their level
    generator_space.sort(key=lambda item: item[1], reverse=True)

    # save generator space on file ordered by level
    file = open(filename,'w')
    for i in range(len(generator_space)):
        g = generator_space[i]
        generator, level = g[0], g[1]
        file.write(generator + ' ' + str(level))
        # record bond structure if available
        if len(bond_structures[generator]) > 0:
            file.write(' ' + bond_structures[generator][0])             
            for i in range(1,len(bond_structures[generator])):
                file.write(',' + bond_structures[generator][i])
        file.write('\n')
    file.close()

    print repr(bond_structures)

    #os.system('')
def save_table_on_file(table,filename):
    file = open(filename,'w')
    for i in table:
        file.write(i)
        for j in table[i]:
            file.write(','+j+':'+repr(table[i][j]))
        file.write('\n')
    file.close()
    
def print_table(table):
    for i in table:
        for j in table[i]:
            print '[' + i + ']' + '[' + j + '] = ' + repr(table[i][j]) + ' '
        print '\n'

def main():    
    split_number = int(sys.argv[1]) # ./train_prior_parameters.py 1 0.5 --> split s1 and 0.5 of the training set
    percentage = float(sys.argv[2])

    training_file_path='/home/students/fillipe//Breakfast_Final'
    root_path_lenth = len(training_file_path.split('/'))
    annotation_file_extensions=['coarse']
    annotation_file_list = read_training_folders(training_file_path,annotation_file_extensions)
    
    #feature_file_path = '../BreakfastII_15fps_qvga_sync'
    #feature_file_extensions = ['_stipdet.txt']
    #feature_file_list = read_training_folders(feature_file_path,feature_file_extensions)
    #delimiters=['_','2']
    label_ignore_list=['SIL']
    
    filtered_training_list = filter_annotation_files(annotation_file_list, split_number)
    sampled_training_list = random_select_items(filtered_training_list, percentage)
    print 'annotation_file_list', len(annotation_file_list), 'filtered_training_list size: ', len(filtered_training_list), 'sampled_training_list size: ', len(sampled_training_list)

    ## read annotation files to find generators, modalities, bond structures
    
    levels = {'action': 3, 'object': 2, 'ingredient':2, 'utensil': 2, 'recipe': 5, 'motion_feature': 1, 'shape_feature': 1}
    modalities = { 'ingredient': ['cereals-o','tea-o','toppping-o','juice-o','dough-o','powder-o','milk-o','teabag-o',
                   'sugar-o', 'orange-o', 'coffee-o', 'oil-o', 'flour-o', 'egg-o', 'water-o', 'glass-o', 'fruit-o', 'bun-o',
                   'pancake-o', 'butter-o', 'toppingOnTop-o', 'saltnpepper-o', 'bunTogether-o'],
                   'utensil': ['cup-o','bowl-o','pan-o','plate-o','squeezer-o', 'knife-o'],
                   'motion_feature': ['hof'],
                   'shape_feature': ['hog'] }
    
    recipes,interactions,actions,objects = parse_annotation_to_find_generators(sampled_training_list)

    modalities['action'] = actions
    #modalities['object'] = [] #objects
    modalities['recipe'] = recipes    
    
    print '\n\n********* Bond Structures **********\n\n'
    
    # adding action and object generators with their bond structures
    bond_structures = create_bond_structure(sampled_training_list,modalities)
   
    # adding feature generators with their bond structures
    bond_structures['hof'] = ['action:out:support']
    bond_structures['hog'] = ['object:out:support']
    
    # save the generator space as a file on disk 
    save_bond_structure_on_file(bond_structures,levels,modalities,'breakfast_generator_space_s'+str(split_number)+'_'+str(percentage)+'.txt')
    
#    find_bond_structures(annotation_file_list, modalities)

    #exit(1)

    # record labels
    file = open('breakfast_labels_s'+str(split_number)+'_'+str(percentage)+'.txt','w')
    for label in actions:
        file.write(label + ' 1\n')
    for label in objects:
        file.write(label + ' 1\n')
    file.close()

    # save list of modalities
    modalities['object'] = objects
    modalities['interaction'] = interactions

    file = open('breakfast_modalities_s'+str(split_number)+'_'+str(percentage)+'.txt','w')
    for key in modalities:
        file.write(key+':')
        for i in range(len(modalities[key])):
            write_data = modalities[key][i]+',' if i < len(modalities[key])-1 else modalities[key][i]
            file.write(write_data)
        file.write('\n')
    file.close()

    #exit(1)

    # construct action x object table
    print 'generate temporal obj obj table'
    table = prepare_table(objects,objects)               
    table = construct_simple_cooccurrence_tables(table,sampled_training_list,True)
    print repr(table)
    print_table(table)
    save_table_on_file(table,'breakfast_temporal_obj-obj_s'+str(split_number)+'_'+str(percentage)+'.txt')  

    print 'generate obj obj table'
    table = prepare_table(objects,objects)
    table = construct_simple_cooccurrence_tables(table,sampled_training_list)
    print repr(table)
    print_table(table)
    save_table_on_file(table,'breakfast_obj-obj_s'+str(split_number)+'_'+str(percentage)+'.txt')  
    
    print 'generate act obj table'
    table = prepare_table(actions,objects)
    table = construct_simple_cooccurrence_tables(table,sampled_training_list)
    save_table_on_file(table,'breakfast_act-obj_s'+str(split_number)+'_'+str(percentage)+'.txt')

    print 'generate interactions actions table'
    table = prepare_table(actions,actions)
    table = construct_simple_cooccurrence_tables(table,sampled_training_list,True)
    save_table_on_file(table,'breakfast_act-act_s'+str(split_number)+'_'+str(percentage)+'.txt')
    
    print 'generate interactions obj table'
    table = prepare_table(interactions,objects)               
    table = construct_simple_cooccurrence_tables(table,sampled_training_list)
    save_table_on_file(table,'breakfast_inter-obj_s'+str(split_number)+'_'+str(percentage)+'.txt')
    
    print 'generate interactions actions table'    
    table = prepare_table(interactions,actions)               
    table = construct_simple_cooccurrence_tables(table,sampled_training_list)
    save_table_on_file(table,'breakfast_inter-act_s'+str(split_number)+'_'+str(percentage)+'.txt')    
    
    print 'generate interactions recipes table'
    table = prepare_table(recipes,interactions)               
    table = construct_simple_cooccurrence_tables(table,sampled_training_list)
    save_table_on_file(table,'breakfast_inter-rec_s'+str(split_number)+'_'+str(percentage)+'.txt')  

    
if __name__ == '__main__':
    main()
