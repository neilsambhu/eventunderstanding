#!/usr/bin/python

import os
import glob
import string

# strategy:
#    read result files and for each video interpretation, find the largest connected component
#        -- read the contents in a table (save edges with dic)
#        -- find the action/actions
#        -- then for each 

def read_baseline(path,videoname):
    filename = path + 'baseline_' + videoname + '.txt'
        
    file = open(filename)
 
    line = file.readline()
    
    numbers = string.split(line.replace('\n',''),',')
    number_of_generators = int(numbers[0])
    number_of_bonds = int(numbers[1])
    
    feature_generators = []
    ontological_generators = {}
    for i in range(number_of_generators):
        # parsing the contents of a line 
        line = file.readline()
        content = string.split(line.replace('\n',''),',')
        id = int(content[0])
        
        # separate feature generators from ontological generators
        if content[3] == 'level2' or content[3] == 'level3':
            # keep generator name and level information, which are indexed by the original generator index
            ontological_generators[id] = [content[1],content[3]]
            
    return ontological_generators

def read_ground_truth(filename):
    file = open(filename)
    line = file.readline()
    numbers = string.split(line.replace('\n',''),',')
    number_of_generators = int(numbers[0])
    number_of_bonds = int(numbers[1])
    
    generators = {}
    # read generators
    for i in range(number_of_generators):
        line = file.readline()
        content = string.split(line.replace('\n',''),',')
        data = string.split(content[1],'_')
        # if the name of the generator does not follow the
        if content[2] == 'level2' and len(data) < 2:
            continue    
        else:    
            id = int(content[0])
            generators[id] = [content[1],content[3]]
    
    bonds = {}
    not_added_bonds = {}
    # read bonds           
    for i in range(number_of_bonds):
        line = file.readline()
        content = string.split(line.replace('\n',''),',')
        src = int(content[0])
        dst = int(content[1])
        if src in generators:
            if generators[src][1] == "level3":
                if src not in bonds:
                    bonds[src] = []
                bonds[src].append(dst)
            else:
                if src not in not_added_bonds:
                    not_added_bonds[src] = []
                not_added_bonds[src].append(dst)
                
#                for generator_index in bonds:
#                    if src in bonds[generator_index] or dst in bonds[generator_index]:
#                        if src not in bonds:
#                            bonds[src] = []
#                        bonds[src].append(dst)       
#                        break
    file.close()
    
    # correct coverage that is not captured by code above
    for src in not_added_bonds:
        for generator_index in bonds:
            if src in bonds[generator_index] or dst in bonds[generator_index]:
                if src not in bonds:
                    bonds[src] = []
                bonds[src].append(dst)       
                break

    active_objects = []    
    for generator_index in bonds:        
        if generator_index not in active_objects:
            active_objects.append(generator_index)
            for dst in bonds[generator_index]:
                active_objects.append(dst)
    
    active_objects = list(set(active_objects))
                    
#    print filename + ' - active objects: ' + repr(active_objects)
    
    return (generators,active_objects)
    
def read_algorithm_response(path,videoname,type='rank1'):
    
    filename = path + videoname + '_best_config_rank1.txt'
    if type == 'baseline':
        filename = path + 'baseline_' + videoname + '.txt'
    file = open(filename)
 
    line = file.readline()
    
    numbers = string.split(line.replace('\n',''),',')
    number_of_generators = int(numbers[0])
    number_of_bonds = int(numbers[1])
    
    feature_generators = []
    ontological_generators = {}
    for i in range(number_of_generators):
        # parsing the contents of a line 
        line = file.readline()
        content = string.split(line.replace('\n',''),',')
        id = int(content[0])
        
        # separate feature generators from ontological generators
        if content[3] == 'level1':
            feature_generators.append(id)    
        else:
            # keep generator name and level information, which are indexed by the original generator index
            ontological_generators[id] = [content[1],content[3]]
            
    ### try to also identify the largest connected component
    feature_bonds = {}
    ontological_bonds = {}
    not_added_bonds = {}
    # read bonds           
    for i in range(number_of_bonds):
        # parsing the contents of a line
        line = file.readline()
        content = string.split(line.replace('\n',''),',')
        src = int(content[0]) # out-bond generator index
        dst = int(content[1]) # in-bond generator index
        if src in ontological_generators and dst in ontological_generators:
            if ontological_generators[src][1] == "level3":
                if src not in ontological_bonds:
                    ontological_bonds[src] = []
                ontological_bonds[src].append(dst)
            else:
                if src not in not_added_bonds:
                    not_added_bonds[src] = []
                not_added_bonds[src].append(dst)
        else:
            feature_bonds[dst] = src
    
    file.close()        
    
#    print 'not added bonds: ' + repr(not_added_bonds) 
    
    # correct coverage that is not captured by code above
    for src in not_added_bonds:
        dst = not_added_bonds[src][0]
        for generator_index in ontological_bonds:
            if src in ontological_bonds[generator_index] or dst in ontological_bonds[generator_index]:
                if src not in ontological_bonds:
                    ontological_bonds[src] = []
                ontological_bonds[src].append(dst)       
                break
                
#    print 'ontological bonds: ' + repr(ontological_bonds)    
        
    active_objects = []    
    for generator_index in ontological_bonds:        
        if generator_index not in active_objects:
            active_objects.append(generator_index)
            for dst in ontological_bonds[generator_index]:
                active_objects.append(dst)
    
    active_objects = list(set(active_objects))
    
#    print 'generators: ' + repr(ontological_generators) + ' active objects: ' + repr(active_objects)
    
    return (ontological_generators,feature_bonds,active_objects)

def main():
    output_file = open('complete_performance_with_clutter_exp3400.csv','w')
    result_path = 'results_config_exp3400/'
    
    
    for filename in glob.glob( os.path.join('useable_files/', '*.txt') ):
        # read data from ground truth file
        (gt_generators, active_objects) = read_ground_truth(filename)
        
        # get the video clip name
        filename_parts = string.split(filename,'.')
        names = string.split(filename_parts[0],'/')
        videoname = names[len(names)-1]
        
        # read algorithm output for the same set of features
        if os.path.isdir(result_path + videoname + '/') == True:
            (output_generators, feature_bonds, output_active_generators) = read_algorithm_response(result_path + videoname + '/',videoname)
            baseline_ontological_generators = read_baseline(result_path + videoname + '/',videoname)
            # (baseline_output_generators, baseline_feature_bonds, baseline_output_active_generators) = read_algorithm_response('results_config_exp3400/' + videoname + '/',videoname,'baseline')
        else:
            continue

        # sort the generators ids
        generators = {}
        keylist = feature_bonds.keys()
        keylist.sort()
        
        # Re-index the ontological generators according to the feature generator's index increasing order
        index = 1
        reindexed_active_objects = []
        for key in keylist:
            # get ['labelname','levelX']
            generators[index] = output_generators[feature_bonds[key]]
            if feature_bonds[key] in output_active_generators:
                reindexed_active_objects.append(index)
            index += 1   
            
        if len(reindexed_active_objects) < 1:
            print videoname + repr(feature_bonds) + ' active generators: ' + repr(output_active_generators)
            continue
         
#        print 'generators: ' + repr(generators) + ' output active objects: ' + repr(reindexed_active_objects)
        
        total_ontological_generators = 1.0*len(output_generators)
        
        intersection = list(set(active_objects) & set(reindexed_active_objects))
       
        # collect ground truth labels
        ground_truth_labels = []
        for object_index in active_objects:
            assigned_label = string.split(gt_generators[object_index][0],'_')
            ground_truth_labels.append(assigned_label[0])
    
        # compute hits of the baseline
        baseline_hits = 0.0
        for key in baseline_ontological_generators:
            if baseline_ontological_generators[key][0] in ground_truth_labels:
                ground_truth_labels.remove(baseline_ontological_generators[key][0])
                baseline_hits += 1.0
            
        # collect ground truth labels
        ground_truth_labels = []
        for object_index in active_objects:
            assigned_label = string.split(gt_generators[object_index][0],'_')
            ground_truth_labels.append(assigned_label[0])
    
        # compute hits of the output
        hits = 0.0
        #print 'generators: ' + repr(generators)
        #print 'ground_truth_labels: ' + repr(ground_truth_labels) 
        for object_index in reindexed_active_objects:
            if generators[object_index][0] in ground_truth_labels:
#                print 'ground_truth_labels: ' + repr(ground_truth_labels) 
                ground_truth_labels.remove(generators[object_index][0])  
#                print 'ground_truth_labels: ' + repr(ground_truth_labels)   
                hits += 1.0   
                     
                
#        print 'hits ' + repr(hits) + ' len(reindexed_active_objects) ' + repr(len(reindexed_active_objects)) + ' hits/len(reindexed_active_objects) ' + repr(hits/len(reindexed_active_objects))        
        precision = hits/len(reindexed_active_objects)
        baseline_precision = baseline_hits/len(baseline_ontological_generators)
        
#        print 'hits ' + repr(hits) + ' len(active_objects) ' + repr(len(active_objects)) + ' hits/len(active_objects) ' + repr(hits/len(active_objects))
        recall = hits/len(active_objects)
        baseline_recall = baseline_hits/len(active_objects)
        
       # print 'len(intersection): ' + repr(len(intersection)) + ' len(reindexed): ' + repr(len(reindexed_active_objects)) + ' len(active_objects) ' + repr(len(active_objects))
        precision_with_features = (hits + len(intersection))/(2.0*len(reindexed_active_objects))
        recall_with_features = (hits + len(intersection))/(2.0*len(active_objects))
        
        precision_of_features = len(intersection)/(1.0*len(reindexed_active_objects))
        recall_of_features = len(intersection)/(1.0*len(active_objects))
        
#        print '### intersection: ' + repr(intersection) + ' precision: ' + repr(count/total_ontological_generators) + ' false discovery rate: ' + repr(1.0-(count/total_ontological_generators))
        
        amount_of_clutter = (1.0*len(active_objects))/total_ontological_generators
        
        if amount_of_clutter > 1.0:
            print videoname  + ' clutter: ' + repr(1.0 - (len(active_objects)/total_ontological_generators))           
        else:
#            repr(baseline_recall) + ',' + repr(baseline_precision) + 
            output_file.write(videoname + ',' + repr(1.0-amount_of_clutter) + ',' + repr(baseline_recall) + ',' + repr(baseline_precision) + ',' +repr(recall) + ',' + repr(precision) + ',' + repr(recall_with_features) + ',' + repr(precision_with_features) + ',' + repr(recall_of_features) + ',' + repr(precision_of_features) + '\n')
        
#        exceeding_number_of_features = len(feature_bonds) - len(active_objects)
#        if exceeding_number_of_features > 0:
#           output_file.write(repr(exceeding_number_of_features) + ',' + repr(count/total_ontological_generators) + ',' + repr(1.0-(count/total_ontological_generators)) + ',' + repr(len(intersection)/total_ontological_generators) + '\n')
#        else:
#            print videoname
            
    output_file.close()        
        
if __name__ == '__main__':
    main()