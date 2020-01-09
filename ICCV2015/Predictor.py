#!/usr/bin/python

# Parent class for other 
class Predictor(object):
    def __init__(self,method,feature):
        self.__method = method
        self.__feature = feature

    def __repr__(self):
        print 'predictor'
        print 'method: ' + self.__method
        print 'feature: ' + self.__feature

    def get_method(self):
        return self.__method

    def get_feature(self):
        return self.__feature

    # This method has to be overridden
    def run(self,g_i,g_j):
        return 0.0
		