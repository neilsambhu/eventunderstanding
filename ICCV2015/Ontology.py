#!/usr/bin/python

from Generator import *
import string

class Ontology:

    ######################################################################################
    ## The pattern classes file lists all labels, their corresponding modalities
    ## and their level of abstraction. The hierarchy of levels determines a natural
    ## order of "dependencies" (I might have to find another word to describe the same).
    ##
    ## The file is expected to have the following structure:
    ##    label_name;3;mod4;val1,val2,val3,val4
    ##    label_name;2;mod1,mod2;val1,val2,val3,val4
    ##    label_name;2;mod1;val1,val2,val3,val4
    ##    label_name;1;mod0;val1,val2,val3,val4
    ##    label_name;1;mod0;val1,val2,val3,val4
    ##

    def __init__(self,ontology_filename):
        self.__labels = []
        self.__levels = {}
        self.__modalities = {}
        self.__bond_structure = {}
        self.__prior = []
        self.__read_labels_filename(ontology_filename)

    #'generator_space_new.txt','youcook_modalities.txt','youcook_strict_ontology.txt',
    #'labels2.txt','youcook_classifiers_new.txt','youcook_multiclass_classifiers.txt',
    #'bags_of_features_setup.txt','youcook_domain_knowledge.txt'

    def __init__(self,gspace_filename,modalities_filename,priors_filename):
        self.__labels = []
        self.__levels = {}
        self.__modalities = {}
        self.__bond_structure = {}
        self.__prior = {}
        self.__time_based_prior = {}
        self.__read_gspace(gspace_filename)
        self.__read_modalities(modalities_filename)
        self.__read_priors(priors_filename)

    #  file format:
    #  <filename 1> <tablename 1> <type=regular/time>
    #  <filename 2> <tablename 2> <type=regular/time>
    #  ...
    #  <filename n> <tablename n> <type=regular/time>
    def __read_priors(self,filename):
        file = open(filename)
        for line in file:
            prior_filename = line.strip().split()[0]
            name = line.strip().split()[1]
            type = line.strip().split()[2]
            self.add_prior(prior_filename,name,type)
        file.close()

    def __read_modalities(self,filename):
        file = open(filename)
        for line in file:
            data = string.split(line.replace('\n',''),':')
            content = string.split(data[1],',')
            for i in range(len(content)):
                if content[i] not in self.__modalities:
                    self.__modalities[content[i]] = []
                self.__modalities[content[i]].append(data[0])
        file.close()
        #print 'Modalities'
        #print repr(self.__modalities)

    def __read_gspace(self, filename):
        file = open(filename,'r')
        for line in file:
            #print line.strip()
            data = string.split(line.replace('\n',''))
            label_name = data[0]
            level = int(data[1])
            self.__labels.append(label_name)
            self.__levels[label_name] = level
            if label_name not in self.__bond_structure:
                    self.__bond_structure[label_name] = []
            if len(data) > 2:
                content = string.split(data[2],',')
                for i in range(len(content)):
                    bond_value = content[i].split(':')[0]
                    bond_type = content[i].split(':')[2]
                    bond_marker = content[i].split(':')[1]
                    self.__bond_structure[label_name].append([bond_value,bond_type,bond_marker])
        file.close()
        #print 'Bond structures:'
        #print repr(self.__bond_structure)

    def __read_labels_filename(self, filename):
        file = open(filename,'r')
        for line in file:
            data = string.split(line.replace('\n',''),';')
            for i in range(len(data)):
                if i == 0:
                    label_name = data[i]
                    self.__labels.append(label_name)
                elif i == 1:
                    level = int(data[1])
                    self.__levels.append(label_name)
                elif i == 2:
                    modalities = string.split(data[2],',')
                    for val in modalities:
                        if label_name not in self.__modalities:
                            self.__modalities[label_name] = []
                        self.__modalities[label_name].append(val)
                elif i == 3:
                    outbonds = string.split(data[3],',')
                    for val in outbonds:
                        if label_name not in self.__bond_structure:
                            self.__bond_structure[label_name] = []
                        self.__bond_structure[label_name].append(val)
        file.close()

    # bond_types: 'natural', 'temporal', 'contextual'
    def obeys_constraints(self,label_i,label_j):
        for mod in self.__modalities[label_j]:
            if mod in self.__bond_structure[label_i]:
                return True
        return False

    def get_bond_structures(self):
        return self.__bond_structure

    def get_bond_structure(self,label):
        return self.__bond_structure[label]

    def get_labels_per_modality(self,modality):
        search_result = []
        for label in self.__modalities:
            if modality in self.__modalities[label]:
                search_result.append(label)
        return search_result

    #
    def get_labels_from_level(self,from_level=5):
        labels_in_level = []
        for label in self.__levels:
            if self.__levels[label] == from_level:
                labels_in_level.append(label)
        return labels_in_level

    def get_same_level_labels(self,label_name):
        same_level_labels = []
        label_level = self.__levels[label_name]
        for label in self.__levels:
            if label != label_name and self.__levels[label] == label_level:
                same_level_labels.append(label)
        return same_level_labels

    def get_equivalent_labels(self,label_name):
        equivalent_labels = []
        label_modalities = self.__modalities[label_name]
        #		print label_name + ' modalities: '+repr(label_modalities)
        for label in self.__modalities:
            if label != label_name and label in self.__labels:
                for mod in label_modalities:
                    if mod in self.__modalities[label]:
                        equivalent_labels.append(label)
                        break
        return equivalent_labels

    def get_modalities(self,label_name):
        modalities = []
        if label_name in self.__modalities:
            for mod in self.__modalities[label_name]:
                modalities.append(mod)
        return modalities

    def add_prior(self,filename,name,type='regular'):
        new_prior = {}
        file = open(filename)
        for line in file:
            line = line.replace('\n','')
            data = string.split(line,',')
            first_key = data[0]
            new_prior[first_key] = {}
            for i in range(1,len(data)):
                content = string.split(data[i],':')
                new_prior[first_key][content[0]] = float(content[1])
        file.close()
        if type == 'time':
            self.__time_based_prior[name] = new_prior
        else:
            self.__prior[name] = new_prior

    def get_labels(self):
        #labels = []
        #for i in range(len(self.__labels)):
        #    labels.append(self.__labels[i])
        return self.__labels

    def get_level(self,label_name):
        return self.__levels[label_name]

    def get_table_name(self,label_i,label_j,time_based=False):
        if not time_based:
            for table_name in self.__prior:
                if label_i in self.__prior[table_name]:
                    if label_j in self.__prior[table_name][label_i]:
                        return table_name
        else:
            for table_name in self.__time_based_prior:
                if label_i in self.__time_based_prior[table_name]:
                    if label_j in self.__time_based_prior[table_name][label_i]:
                        return table_name

        return None

    # to use this table, the name of the table needs to be known and passed as an argument
    def conditional_occurrence(self,table_name,label,time_based=False,order=2):
        conditional_values = {}
        table = None
        if not time_based:
            if table_name not in self.__prior:
                return conditional_values
            table = self.__prior[table_name]
        else:
            if table_name not in self.__time_based_prior:
                return conditional_values
            table = self.__time_based_prior[table_name]

        if order == 1:
            if label not in table:
                return conditional_values

            for key in table[label]:
                if key != label:
                    conditional_values[key] = table[label][key]
        else:
            any_key = table.keys()[0]
            if label not in table[any_key]:
                return conditional_values

            for key in table:
                if key != label:
                    conditional_values[key] = table[key][label]

        return conditional_values

    def time_based_prior(self,label_i,label_j):
        validity = False

        for table in self.__time_based_prior:
            if label_i in self.__time_based_prior[table]:
                if label_j in self.__time_based_prior[table][label_i]:
                    return self.__time_based_prior[table][label_i][label_j],True

        for table in self.__time_based_prior:
            if label_j in self.__time_based_prior[table]:
                if label_i in self.__time_based_prior[table][label_j]:
                    return self.__time_based_prior[table][label_j][label_i],True

        return 0.0,validity

    def gtime_based_prior(self,g_i,g_j,config):
        label_i = g_i.get_name()
        label_j = g_j.get_name()
        if self.__intersect(['actions','objects'],g_i.get_modality()):
            label_i = self.__get_interaction_name(g_i,config)

        for table in self.__time_based_prior:
            if label_i in self.__time_based_prior[table]:
                if label_j in self.__time_based_prior[table][label_i]:
                    return self.__time_based_prior[table][label_i][label_j]

        label_i = g_i.get_name()
        label_j = g_j.get_name()
        if self.__intersect(['actions','objects'],g_j.get_modality()):
            label_j = self.__get_interaction_name(g_j,config)

        for table in self.__time_based_prior:
            if label_j in self.__time_based_prior[table]:
                if label_i in self.__time_based_prior[table][label_j]:
                    return self.__time_based_prior[table][label_j][label_i]

        return 0.0

    def prior(self,label_i,label_j):
        for table in self.__prior:
            if label_i in self.__prior[table]:
                if label_j in self.__prior[table][label_i]:
                    #print 'table',table
                    return self.__prior[table][label_i][label_j],True

        for table in self.__prior:
            if label_j in self.__prior[table]:
                if label_i in self.__prior[table][label_j]:
                    #print 'table',table
                    return self.__prior[table][label_j][label_i],True

        return 0.0,False

    def __intersect(self,list_a,list_b):
        return list(set(list_a) & set(list_b))

    def __get_interaction_name(self,g_k,config):
        label = g_k.get_name()
        if g_k.get_level() == 'level3':
            connected_objects = []
            for outbond in g_k.get_outbonds():
                if outbond.get_connector() != None:
                    g_t = config.get_generator_by(outbond.get_connector())
                    if g_t.get_level() == g_k.get_level()-1:
                        connected_objects.append(g_t.get_name())
            label += '_' + connected_objects[random.sample(len(connected_objects),1)[0]]
            del connected_objects
        elif g_k.get_level() == 'level2':
            for inbond in g_k.get_inbonds():
                # if an inbond exists, then there is a connector (the same is not true for outbonds)
                g_t = config.get_generator_by(inbond.get_connector())
                if 'actions' in g_t.get_modality():
                    label = g_t.get_name() + '_' + label
                    break
        return label

    def gprior(self,g_i,g_j,config):
        label_i = g_i.get_name()
        label_j = g_j.get_name()
        if self.__intersect(['actions','objects'],g_i.get_modality()) and 'recipes' in g_j.get_modality():
            label_i = self.__get_interaction_name(g_i,config)
        elif self.__intersect(['actions','objects'],g_j.get_modality()) and 'recipes' in g_i.get_modality():
            label_j = self.__get_interaction_name(g_j,config)

            for table in self.__prior:
                if label_i in self.__prior[table]:
                    if label_j in self.__prior[table][label_i]:
                        return self.__prior[table][label_i][label_j]

            for table in self.__prior:
                if label_j in self.__prior[table]:
                    if label_i in self.__prior[table][label_j]:
                        return self.__prior[table][label_j][label_i]
