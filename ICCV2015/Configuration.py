#!/usr/bin/python

from Generator import *
import copy
import os

class Configuration:
    def __init__(self):
        self.__max_number_of_inbonds = 0
        self.__generators = []
        self.__ontological_generators = None
        self.__feature_generators = None
        self.__type = None       # 'master' or 'slave'
        self.__time = -1
        self.__generator_ids = []
        self.__generators_by_id = {}
        self.__number_of_generators_by_level = {}   # a counter of generators from different levels

    def add_generator(self, g):
        if g.get_id() not in self.__generator_ids:
            n = len(self.__generators)
            #print 'new length: ',repr(n)
            self.__generators.append(g)
            self.__generator_ids.append(g.get_id())
            if g.get_level() not in self.__number_of_generators_by_level:
                self.__number_of_generators_by_level[g.get_level()] = 0
            self.__number_of_generators_by_level[g.get_level()] += 1
        #    self.__generators_by_id[g.get_id()] = g
        #			if len(self.__generators) > n:
        #				print 'new generator added: ' + repr(g) + ' id: ' + repr(g.get_id())
        #				print 'count: ' + repr(len(self.__generators))
        #print repr(self.__generators)

    def get_copy(self):
        c = Configuration()
        for i in range(len(self.__generators)):
            c.add_generator(self.__generators[i].get_copy())
        c.set_current_time(self.__time)
        c.set_level_cardinality(self.__number_of_generators_by_level)
        return c

    def set_level_cardinality(self,level_cardinality):
        self.__number_of_generators_by_level = {}
        for key in level_cardinality:
            self.__number_of_generators_by_level[key] = level_cardinality[key]

    def replace(self, g_target, g_new):
        c = self.get_copy()
        # to remove interaction generator that connect to the generator being removed
        for bond in g_target.get_inbonds():
            g = self.get_generator_by(bond.get_connector())
            if g.get_level() > 3:
                c.remove_generator(g.get_id())
        #print 'replace #',g_target.get_id(),g_target.get_name(),'by #',g_new.get_id(),g_new.get_name()
        c.remove_generator(g_target.get_id())
        c.add_generator(g_new)
        return c

    # revise this function
    def remove_generator(self,g_id):
        # look for the target generator to be removed
        for i in range(len(self.__generators)):
            # if the target generator is found
            if self.__generators[i].get_id() == g_id:
                # remove its connections with other generators in this configuration
                inbonds = self.__generators[i].get_inbonds()
                for j in range(len(inbonds)):
                    # remove connector (or generator) by id
                    g_j = self.get_generator_by(inbonds[j].get_connector())
                    # open closed out-bond of a generator that is connecting to the one being removed
                    g_j.disconnect_outbond(g_id)
                # remove all bonds the generator -- what's the purpose of this?
                self.__generators[i].remove_bonds()
                #g_i = self.__generators[i]
                self.__number_of_generators_by_level[self.__generators[i].get_level()] -= 1
                del self.__generators[i]
                #del g_i
                break

        # remove inbonds
        for i in range(len(self.__generators)):
            inbonds = self.__generators[i].get_inbonds()
            for j in range(len(inbonds)):
                if inbonds[j].get_connector() == g_id:
                    del inbonds[j]
                    break

        # finally, update the list of generator ids
        for i in range(len(self.__generator_ids)):
            if self.__generator_ids[i] == g_id:
                del self.__generator_ids[i]
                break

    def remove_bonds(self):
        for i in range(len(self.__generators)):
            self.__generators[i].remove_bonds()

    def remove_generators(self):
        del self.__generators[:]
        del self.__ontological_generators
        del self.__feature_generators
        del self.__number_of_generators_by_level
        self.__ontological_generators = None
        self.__feature_generators = None
        self.__number_of_generators_by_level = {}

    # mode: 'id', 'name', 'level'
    def get_generator_by(self,search_key,mode='id'):
        matches = []
        for i in range(len(self.__generators)):
#            print 'g_id: ' + repr(self.__generators[i].get_id()) + ' name: ' + repr(self.__generators[i].get_name()) + ' ' + repr(self.__generators[i].get_level())
            if mode == 'id' and self.__generators[i].get_id() == search_key:
#                print 'key found ' + repr(self.__generators[i])
                return self.__generators[i]
            elif mode == 'name' and self.__generators[i].get_name() == search_key:
#                print 'hi 2'
                matches.append(self.__generators[i])
            elif mode == 'level' and self.__generators[i].get_level() == search_key:
 #               print 'hi 3'
                matches.append(self.__generators[i])
  #      print 'no search case found'
        return matches

    # attempts to close a bond in one particular direction, if not possible it will return
    # order of connections should be treated in the proposal function implementation
    def close_bonds(self, i, j, energy, time_based_bond=False, strict_mode=True):
        #		print 'search for g_i'
        g_i = self.get_generator_by(i, 'id')
        #		print 'g_i = ' + repr(g_i)
        g_j = self.get_generator_by(j, 'id')
        #		print 'closing g_i='+repr(g_i.get_name())+':'+repr(g_i.get_id())+' g_j='+repr(g_j.get_name())+':'+repr(g_j.get_id())
        status = g_i.close_outbond(g_j, energy, time_based_bond, strict_mode)
        #if status:
        #    print 'close bond ('+g_i.get_name()+','+g_j.get_name()+'), energy:'+repr(energy)+' closed? '+str(status)
        return status

    def is_equal(self, config):
        local_generators = []
        external_generators = []
        feature_generators = self.get_feature_generators()
        #feature_generators_2 = config.get_feature_generators()
        for i in range(len(feature_generators)):
            # get outbonds of local feature generator
            outbonds = feature_generators[i].get_outbonds()

            # get feature generator from external configuration that has the same id
            g_f = config.get_generator_by(feature_generators[i].get_id(), 'id')
            g_f_outbonds = g_f.get_outbonds()

            if len(outbonds) != len(g_f_outbonds):
                return False

            for j in range(len(outbonds)):
                g_j = self.get_generator_by(outbonds[j].get_connector())
                local_generators.append(g_j.get_name())

            for k in range(len(g_f_outbonds)):
                g_k = config.get_generator_by(g_f_outbonds[k].get_connector())
                external_generators.append(g_k.get_name())

        if len(local_generators) != len(external_generators): return False

        no_intersects = 0
        intersection = list(set(local_generators) & set(external_generators))
        no_intersects += len(intersection)
        while len(intersection) > 0:
            for concept in intersection: local_generators.remove(concept)
            for concept in intersection: external_generators.remove(concept)
            intersection = list(set(local_generators) & set(external_generators))
            no_intersects += len(intersection)

        if no_intersects == len(local_generators): return True

        return False


    # def is_equal(self, config):
    #     feature_generators = self.get_feature_generators()
    #     #feature_generators_2 = config.get_feature_generators()
    #     for i in range(len(feature_generators)):
    #         inbonds = feature_generators[i].get_inbonds()
    #
    #         # get feature generator from external configuration that has the same id
    #         g_f = config.get_generator_by(feature_generators[i].get_id(),'id')
    #         g_f_inbonds = g_f.get_inbonds()
    #
    #         if len(inbonds) != len(g_f_inbonds):
    #             return False
    #
    #         local_generators = []
    #         for j in range(len(inbonds)):
    #             g_j = self.get_generator_by(inbonds[j].get_connector())
    #             local_generators.append(g_j.get_name())
    #
    #         external_generators = []
    #         for k in range(len(g_f_inbonds)):
    #             g_k = config.get_generator_by(g_f_inbonds[k].get_connector())
    #             external_generators.append(g_k.get_name())
    #
    #         intersection = list(set(local_generators) & set(external_generators))
    #         #if len(intersection) < len(inbonds): # old condition
    #         #    return False
    #         if len(intersection) != len(inbonds):
    #             if len(intersection) != len(g_f_inbonds):
    #                 return False
    #
    #     return True

    # another idea to implement the is_equal function:
    #
    #  get inbonds of the feature generator from both configurations
    #  get outbonds of the features generator from both configurations
    #  find the intersections of both cases
    #


    def get_ontological_generators(self):
        self.__ontological_generators = []
        for g in self.__generators:
            if g.get_type() == 'ontological':
                self.__ontological_generators.append(g)
        return self.__ontological_generators

    def get_feature_generators(self):
        self.__feature_generators = []
        for g in self.__generators:
            if g.get_type() == 'feature':
                self.__feature_generators.append(g)
        return self.__feature_generators

    def get_local_energy(self, g, weights=None):
        energy = 0.0
        if g in self.__generators:
            energy = g.get_outbonds_energy(weights) + g.get_inbonds_energy(weights)
        return energy

    def get_energy(self, weights=None):
        energy = 0.0
        ontological_generators = self.get_ontological_generators()
        for g in ontological_generators:
            local_energy = g.get_outbonds_energy(weights)
            energy += local_energy #g.get_outbonds_energy(weights)
            #print 'local energy: ' + repr(local_energy)
            #print 'cummulative energy: ' + repr(energy)
        return energy
		
#	def get_energy(self,weights):
#		energy = 0.0
#		for g in self.__generators:
#			energy += g.get_outbonds_energy(weights)
#		return energy

    def print_info(self):
        print 'Configuration: '
        print '  # of generators: '+repr(len(self.__generators))
        for g in self.__generators:
            g.print_info()

    def set_current_time(self,current_time):
        self.__time = current_time

    def get_current_time(self):
        return self.__time

    def get_generators(self):
        return self.__generators

    def get_max_number_of_inbonds(self):
        max_number_of_inbonds = 0
        for g in self.__generators:
            if g.get_number_of_inbonds() > max_number_of_inbonds:
                max_number_of_inbonds = g.get_number_of_inbonds()
        return max_number_of_inbonds

    def get_number_of_generators(self):
        # total sum of feature generators, total sum of ontological generators
        total = [ 0 , 0 ]
        for generator in self.__generators:
            if generator.get_type() == 'feature':
                total[0] += 1
            elif generator.get_type() == 'ontological':
                total[1] += 1

        return total