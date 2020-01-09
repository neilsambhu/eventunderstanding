#!/usr/bin/python

# Parent class for other 
class Predictor(object):
    def __init__(self, method, feature, tanhk=1.0):
        self.__method = method
        self.__feature = feature
        self.__tanh_k = tanhk;

    def __repr__(self):
        print 'Predictor params:'
        print '-- method: ' + self.__method
        print '-- feature: ' + self.__feature
        print '-- tanh k: ' + self.__tanh_k

    def get_method(self):
        return self.__method

    def get_feature(self):
        return self.__feature;

    def get_tanh_k(self):
        return self.__tanh_k;

    # This method has to be overridden
    def run(self, g_i, g_j):
        return 0.0
		