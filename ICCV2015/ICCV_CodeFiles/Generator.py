#!/usr/bin/python

from Bond import *
import random
import copy
import math

# -------------------------------------------------------------------------------------- #
# The class Generators represents the basic unit for constructing complex patterns in    #
# using the Pattern Theory concepts.													 #
# -------------------------------------------------------------------------------------- #

class Location:
    def __init__(self):
        self.__x_min = 0
        self.__x_max = 0
        self.__y_min = 0
        self.__y_max = 0
        self.__t_min = 0
        self.__t_max = 0
        self.__is_valid = False

    def copy(self, location):
        x_range = location.get_x_range()
        y_range = location.get_y_range()
        t_range = location.get_t_range()
        self.set_x_range(x_range[0], x_range[1])
        self.set_y_range(y_range[0], y_range[1])
        self.set_t_range(t_range[0], t_range[1])

    def get_copy(self):
        loc = Location()
        loc.set_x_range(self.__x_min, self.__x_max)
        loc.set_y_range(self.__y_min, self.__y_max)
        loc.set_t_range(self.__t_min, self.__t_max)
        loc.set_as_valid()
        return loc

    def is_valid(self):
        return self.__is_valid

    def set_as_valid(self):
        self.__is_valid = True

    def set_as_invalid(self):
        self.__is_valid = False

    def set_x_range(self,x_min,x_max):
        self.__x_min = x_min
        self.__x_max = x_max
        self.set_as_valid()

    def set_y_range(self,y_min,y_max):
        self.__y_min = y_min
        self.__y_max = y_max
        self.set_as_valid()

    def set_t_range(self,t_min,t_max):
        self.__t_min = t_min
        self.__t_max = t_max
        self.set_as_valid()

    def get_x_range(self):
        return self.__x_min, self.__x_max

    def get_y_range(self):
        return self.__y_min, self.__y_max

    def get_t_range(self):
        return self.__t_min, self.__t_max

    def spatial_overlap(self, location):
        x_range = location.get_x_range()
        if self.__x_min < x_range[1] and self.__x_max > x_range[0]:
            print 'overlap in x: ',self.__x_min,self.__x_max,repr(x_range)
            y_range = location.get_y_range()
            if self.__y_min < y_range[1] and self.__y_max > y_range[0]:
                print 'overlap in y: ',self.__y_min,self.__y_max,repr(y_range)
                x_overlap = min([self.__x_max, x_range[1]]) - max([self.__x_min, x_range[0]])
                y_overlap = min([self.__y_max, y_range[1]]) - max([self.__y_min, y_range[0]])
                denominator = ((self.__x_max - self.__x_min)*(self.__y_max-self.__y_min))
                relative_overlap_ratio = float(x_overlap * y_overlap) / denominator if denominator > 0.0 else 0.0
                print 'relative overlap: ',relative_overlap_ratio
                return relative_overlap_ratio
        return 0.0


    def temporal_overlap(self, location):
        t_range = location.get_t_range()
        if self.__t_min < t_range[1] and self.__t_max > t_range[0]:
            t_overlap = min([self.__t_max, t_range[1]]) - max([self.__t_min, t_range[0]])
            relative_overlap_ratio = t_overlap / float(self.__t_max - self.__t_min)
            return relative_overlap_ratio
        return 0.0


class Generator:
    # -----------------------------------
    # BASE METHODS
    #
    counter = 0
    busy = []
    free = []

    def __init__(self,name,level,modality,type,cost,time,is_copy=False,id_copy=None):
        self.__location = Location()
        self.__is_match = False
        self.__is_copy = is_copy
        self.__id = Generator.counter
        if is_copy == True:
            self.__id = id_copy
        else:
            Generator.counter += 1

        #		if is_copy == False:
        #			self.__id = Generator.counter
        #			print 'free ids: ' + repr(Generator.free) + ' busy ids: ' + repr(Generator.busy)
        #			if len(Generator.free) > 0:
        #				self.__id = Generator.free.pop()
        #				print 'got one from the free list ' + repr(Generator.free)
        #			else:
        #				Generator.counter += 1
        #			Generator.busy.append(self.__id)
        #			print 'busy ids: ' + repr(Generator.busy)
        #			print 'received id: ' + repr(self.__id)
        #		else:
        #			self.__id = id_copy
        self.__name = name
        self.__level = level
        self.__modality = modality
        self.__type = type # will be used for cvpr2015 paper to know the type of bond and how to quantify it
        self.__cost = cost
        self.__outbonds = []
        self.__inbonds = []
        self.__top_labels = []
        self.__time = time # will be used for cvpr2015 paper, maybe used to compute some bond weights
        self.__duration = 0
        self.__modality_state = None
        self.__feature_path = None
        self.__groundtruth_label = []
        self.__coconcepts = []
        self.__alocation = None
        self.__rlocation = None

    #	print '__init__ updating Generator counter to ' + repr(Generator.counter)

    #	def __del__(self):
    #		if self.__is_copy == False:
    #			Generator.busy.remove(self.__id)
    #			Generator.free.append(self.__id)
    #			Generator.counter -= 1
    #	print '__del__ updating Generator counter to ' + repr(Generator.counter)

    # -----------------------------------
    # PRIVATE USE ONLY METHODS
    #
    def __search_outbond(self, g):
        available_outbonds = []
        for i in range(len(self.__outbonds)):
            #			print 'b_'+repr(i)+': '+self.__outbonds[i].get_value()
            # if the outbond is unconnected and its value is one of g's modality set
            if self.__outbonds[i].get_connector() == None:
                if self.get_type() == 'support': print 'self.name: '+self.get_name()+' value:'+self.__outbonds[i].get_value()+' modalities:'+repr(g.get_modality())
                if self.__outbonds[i].get_value() in g.get_modality() or self.__outbonds[i].get_value() == g.get_name():
                    # then, g can be connected at coordinate i
                    #if self.get_type() == 'feature': print 'will connect '+g.get_name()+' through bond j='+str(i)
                    available_outbonds.append(i)
            #				print 'found coordinate'
            #				return i

        if available_outbonds:
            #if self.get_type() == 'feature': print 'return the bond coordinate'
            return available_outbonds[random.randrange(len(available_outbonds))]

        return None

    def is_inbond_of(self, g):
        inbond = g.get_inbond_coordinate(self.get_id())
        if inbond != None:
            return True
        return False
			
# -----------------------------------
# PUBLIC USE METHODS
# -----------------------------------
#	
# : METHODS THAT CHANGE VALUES OF AN INSTANCE
#	
#	def add_outbond(): only used upon the creation of a generator instance	

    def get_location(self):
        return self.__location

    def copy_location(self, location):
        self.__location = location.get_copy()

    def set_location(self, x_min, x_max, y_min, y_max, t_min, t_max):
        self.__location.set_x_range(x_min, x_max)
        self.__location.set_y_range(y_min, y_max)
        self.__location.set_t_range(t_min, t_max)

    # store feature location information (file path)
    def set_rlocation(self,value):
        self.__rlocation = value

    def set_alocation(self,value):
        self.__alocation = value

    def get_alocation(self):
        return self.__alocation

    def get_rlocation(self):
        return self.__rlocation

    def set_groundtruth_label(self,label):
        self.__groundtruth_label = label

    def get_groundtruth_label(self):
        return self.__groundtruth_label

    def set_feature_path(self,feature_path):
        self.__feature_path = feature_path

    def set_bond_structure(self,bond_structure):
        for bond in bond_structure:
            bond_value = bond[0]
            bond_type = bond[1]
            bond_marker = bond[2]

            if bond_marker == 'out': self.add_outbond(bond_type,bond_value)
            #if bond_marker == 'out': self.add_outbond(bond_type,bond_value)

            # for the case when it is not on strict_mode == True
            self.add_coconcept(bond_value)

    def set_copy_state(self,state):
        self.__is_copy = state

    def set_is_match(self,state):
        self.__is_match = state

    def get_time_duration(self):
        duration = 0.0
        for t in self.__time:
            duration += t
        return duration

    def get_match_state(self):
        return self.__is_match

    def get_copy_state(self):
        return self.__is_copy

    def set_modality_state(self,state):
        self.__modality_state = state #self.__modality.index(state)

    def get_modality_state(self):
        return self.__modality_state

    def add_coconcept(self,concept):
        #print 'adding concept ' + concept
        self.__coconcepts.append(concept)

    def get_coconcepts(self):
        return self.__coconcepts

    def add_outbond(self,type,value):
        bond = Bond(type,value)
        bond.set_marker('out')
        self.__outbonds.append(bond)

    def add_inbond(self,type,g_id,coordinate,energy):
        bond = Bond(type,self.get_modality_state(),coordinate,g_id,energy)
        bond.set_marker('in')
        self.__inbonds.append(bond)

    def add_outbond_copy(self,outbond):
        self.__outbonds.append(outbond)

    def add_inbond_copy(self,inbond):
        self.__inbonds.append(inbond)

    #	def get_local_weight(self,g):
    #		return 0.0001

    def get_spatial_overlap_ratio(self,g):
        return 0.0001

    # this is one of the most expensive functions
    def close_outbond(self, g, energy, time_based_bond=False, strict_mode=True):
        # Check if these generators are already connected
        if self.is_inbond_of(g) or g.is_inbond_of(self):
            #			print 'one is inbond of the other...'
            return False

        # spatial feature must be handled by proposal functions

        #spatial_overlap_ratio = self.get_spatial_overlap_ratio(g)
        #spatial_overlap_energy = math.log(spatial_overlap_ratio,2)

        if strict_mode == True:
            outbond_coordinate = self.__search_outbond(g)

            if outbond_coordinate != None:
                # bonds have to have type so that connections are handled in a more generic manner
                if self.__outbonds[outbond_coordinate].get_type() == 'temporal' and time_based_bond == False: return False

                #inbond_coordinate = g.get_number_of_inbonds()

                #if self.get_type() == 'feature': print 'setting up connection...'
                # complexity_term = g.get_number_of_inbonds() + 1
                # complexity_term_energy = math.log(complexity_term,10)
                # energy += complexity_term_energy/(complexity_term*complexity_term)

                # set the location of the ontological generator according to the location of the features that it explains
                spatial_overlap_energy = 0.0
                if g.get_type() == 'feature' and self.__type == 'ontological':
                    self.__location = g.get_location().get_copy()
                elif g.get_type() == 'ontological' and self.__type == 'feature':
                    print repr(g.get_location())
                    g.get_location().copy(self.__location)
                    print repr(g.get_location()) + ' validity: ' + repr(g.get_location().is_valid())
                elif g.get_type() == 'ontological' and self.__type == 'ontological':
                    print 'Lets connect ' + self.get_name() + ' to ' + g.get_name() + ' ' + repr(self.__location.is_valid()) + ' - ' + repr(g.get_location().is_valid())
                    # here, it is assumed that each ontological generator has a location
                    if self.__location.is_valid() and g.get_location().is_valid():
                        internal_overlap = self.__location.spatial_overlap(g.get_location())
                        external_overlap = self.__location.spatial_overlap(g.get_location())
                        spatial_overlap = max([internal_overlap, external_overlap])
                        spatial_overlap_energy = self.__compute_energy(-self.__thresh_function(spatial_overlap, 0.3),2.0)
                        print 'Connect ' + self.get_name() + ' to ' + g.get_name() + ' ' + repr(spatial_overlap) \
                              + ' ' + repr(spatial_overlap_energy)

                # value = self.__outbonds[outbond_coordinate].get_value()
                bond_type = self.__outbonds[outbond_coordinate].get_type()
                self.__outbonds[outbond_coordinate].set_connector(g.get_id())
                self.__outbonds[outbond_coordinate].set_energy([energy, spatial_overlap_energy])
                #print 'inbonds ',repr(g.get_inbonds())
                g.add_inbond(bond_type, self.__id, outbond_coordinate, [energy, spatial_overlap_energy])
                inbond_coordinate = g.get_number_of_inbonds()-1
                #print 'new coordinate: ',inbond_coordinate
                self.__outbonds[outbond_coordinate].set_connector_coordinate(inbond_coordinate)

                # print "# of inbonds: " + repr(g.get_number_of_inbonds())
                return True # on successful addition

        return False # in case of failure


    def __compute_energy(self, score, k=1.):
        #return math.log(1.0001 - score, 2.0)
        energy = math.tanh(k * score)
        #print 'compute energy with score: ',score,' energy is ',energy
        return energy


    def __thresh_function(self, score, thresh):
        # could be a probability distribution
        if score < thresh: return (-thresh + score)
        return score


    def remove_inbond(self,coordinate):
        if coordinate < len(self.__inbonds):
            bond = self.__inbonds[coordinate]
            del self.__inbonds[coordinate]
            return bond
        return None

    def remove_inbond_by_id(self, g_id):
        for i in range(len(self.__inbonds)):
            if self.__inbonds[i].get_connector() == g_id:
                bond = self.__inbonds[i]
                del self.__inbonds[i]
                return bond
        return None

    def disconnect_outbond(self,g_id):
        for i in range(len(self.__outbonds)):
            if self.__outbonds[i].get_connector() == g_id:
                self.__outbonds[i].remove_connector()
                return True
        return False


    def remove_bonds(self):
        del self.__inbonds
        self.__inbonds = []
        for i in range(len(self.__outbonds)):
            self.__outbonds[i].remove_connector()


    # Methods add_top_label and get_kth_best_label are only used for feature generators
    def add_top_label(self, label):
        self.__top_labels.append(label)


    def get_top_labels(self):
        return self.__top_labels


    def get_kth_best_label(self,k):
        return self.__top_labels[k]


    # :	METHODS THAT DO NOT CHANGE THE STATE OF AN INSTANCE
    def get_outbond_by_coordinate(self, coordinate):
        if coordinate < len(self.__outbonds):
            return self.__outbonds[coordinate]
        return None


    def get_features(self):
        return self.__feature_path


    def get_name(self):
        return self.__name


    def get_id(self):
        return self.__id


    def get_level(self):
        return self.__level

    def get_modality(self):
        return self.__modality

    def get_cost(self):
        return self.__cost

    def get_type(self):
        return self.__type

    def get_time(self):
        self.__time.sort()
        return self.__time

    def get_bond_weight(self,weights=None,modality=None):
        if weights == None:
            return 1.0
        else:
            if modality == None:
                modality = self.__modality

            visited = False
            weight = 0.0
            count = len(modality)
            for key in weights:
                if key in modality:
                    weight += ( (1./count) * weights[key] )
                    visited = True

            if visited == False:
                weight = 1.0

            return weight

    def get_outbonds_energy(self,weights=None):
        energy = 0.0
        for bond in self.__outbonds:
            #weight = self.get_bond_weight(weights,[bond.get_value()])

            weight = 1. if bond.get_type() not in weights else weights[bond.get_type()]
            #			print 'source generator: ' + self.get_name() + '   ' + repr(bond.get_value()) + ' weight: ' + repr(weight) + ' energy: ' + repr(bond.get_energy()) + ' wenergy: ' + repr(bond.get_energy(weight))
            energy += bond.get_energy(weight)
        return energy

    def get_inbonds_energy(self,weights=None):
        energy = 0.0
        for bond in self.__inbonds:
            #weight = self.get_bond_weight(weights)
            weight = 1. if bond.get_type() not in weights else weights[bond.get_type()]
            energy += bond.get_energy(weight)
        return energy

    def get_modality(self):
        return self.__modality

    def get_number_of_inbonds(self):
        return len(self.__inbonds)

    def get_inbond_coordinate(self,connector):
        for i in range(len(self.__inbonds)):
            if self.__inbonds[i].get_connector() == connector:
                return i
        return None

    def get_copy(self):
        g = Generator(self.__name,self.__level,
                      copy.deepcopy(self.__modality),
                      self.__type,self.__cost,copy.deepcopy(self.__time),True,self.__id)

        for i in range(len(self.__inbonds)):
            g.add_inbond_copy(self.__inbonds[i].get_copy())

        for i in range(len(self.__outbonds)):
            g.add_outbond_copy(self.__outbonds[i].get_copy())

        for i in range(len(self.__coconcepts)):
            g.add_coconcept(self.__coconcepts[i])

        for i in range(len(self.__top_labels)):
            g.add_top_label(self.__top_labels[i])

        g.set_feature_path(self.get_features())
        g.set_modality_state(self.get_modality_state())
        g.set_groundtruth_label(self.get_groundtruth_label())
        g.set_is_match(self.get_match_state())
        g.set_alocation(self.get_alocation())
        g.set_rlocation(self.get_rlocation())

        g.copy_location(self.get_location())

        return g

    def get_inbonds(self):
        return self.__inbonds

    def get_outbonds(self):
        return self.__outbonds

    def print_info(self):
        info_string = '    Generator #'+repr(self.__id)+' = name:'+self.__name+' type: '+self.__type
        info_string += ', level:'+repr(self.__level)+', type:'+self.__type+', modality:'+repr(self.__modality)
        print info_string
        for bond in self.__inbonds:
            bond.print_info()
        for bond in self.__outbonds:
            bond.print_info()
	
