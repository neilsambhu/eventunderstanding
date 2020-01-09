#!/usr/bin/python

import numpy as np
from operator import itemgetter, attrgetter
import random
import os

class FeatureHandler:
    def __init__(self):
        pass

    def test_x(self, x, current_x):
	    # if x is empty, no constraints need to be tested
	    if not x:
		    return True
	    if x[0] <= current_x and current_x <= x[1]:
		    return True
	    return False

    def test_y(self, y, current_y):
	    # if y is empty, no constraints need to be tested
	    if not y:
		    return True
	    if y[0] <= current_y and current_y <= y[1]:
		    return True
	    return False

    def test_t(self, t, current_t):
	    # if t is empty, no constraints need to be tested
	    if not t:
		    return True
	    if t[0] <= current_t and current_t <= t[1]:
		    return True
	    return False
	
#	def read_sample(self, filename);
#	    pass

#		    file = open(filename)
#		    for line in file:
#		        if not line.startswith('#'):
#		            pass
#		    file.close()
	    	    
#	def build_dicionary(self, file_list=[], dict_size=400):
#	    for filename in file_list:
#	        file = open(filename,'r')
#	        file.close()

    # specify constraints for y, x, and t as pairs of lower and upper bounds, inclusive(?)
    # e.g. y=[1,100], t=[5,25]
    def parse_features(self, filename_read="features.txt", filename_write="feature_data.txt", file_mode='w', feature_type=['hog','hof'], x=[],y=[],t=[], sampling_rate=1., xyt=True):	
	    feature_vectors = []
	    try:
		    with open(filename_read, 'r') as features:
			    with open(filename_write, file_mode) as outfile:
				    # makes comment at top of page
				    #outfile.write('# key: y x t hog(72) hof(90)')
				    #outfile.write('\n')

				    for line in features:
					    # if line is not a comment
					    if not line.startswith('#'):
						    line = line.strip().split()
						    # height, width, time
						    current_y, current_x, current_t = line[4:7]
						    if self.test_x(x, int(current_x)) and self.test_y(y, int(current_y)) and self.test_t(t, int(current_t)):
							    #if xyt == True:
							    #    outfile.write(current_y+' '+current_x+' '+current_t+' ')
							    
							    # hog starts at 9th element
							    if feature_type == ['hog','hof']:
								    #outfile.write(' '.join(line[9:])+'\n')
								    feature_vectors.append(line[4:7]+line[9:])
							    # hog is 72 elements long
							    elif feature_type == ['hog']:
								    #outfile.write(' '.join(line[9:81])+'\n')
								    feature_vectors.append(line[4:7]+line[9:81])
							    # hof is from 81st element to end of list
							    elif feature_type == ['hof']:
							        #outfile.write(' '.join(line[81:])+'\n')
							        feature_vectors.append(line[4:7]+line[81:])
                    
				    #idx = np.argsort(feature_vectors[:][2])
				    feature_vectors = sorted(feature_vectors, key=itemgetter(2,1,0))
				    total_number_of_features = len(feature_vectors)
				    sampling_size = int(total_number_of_features * sampling_rate)
				    selected_features_indices = random.sample(range(total_number_of_features), sampling_size)
				     				    
#				    for i in range(len(feature_vectors)):
				    for i in selected_features_indices:
				        outfile.write(' '.join(feature_vectors[i])+'\n')
				    
				    print("File", filename_write, "created successfully", os.getcwd())
				    
				    del feature_vectors

	    except OSError:
		    print("File", filename_read, "not found!")
		    
		

    # specify k, the size of the sample of features you wish to take
    
    def count_lines(self, filename):
        num_lines = sum(1 for line in open(filename) if not line.rstrip()) 
        return num_lines
    
    def random_sample(self, k, filename_read ="feature_data.txt", filename_write="random_sample.txt"):
	    random.seed()
	    try:
		    with open(filename_read, 'r') as features:
			    with open(filename_write, 'w') as outfile:
				    # gets all lines in file that aren't comments
				    lines = [line.strip().split() for line in features if not line.startswith('#')]
				    sample = random.sample(lines, k)

				    # makes comment at top of page
				    outfile.write('# random_sample size of ' + str(k) + " features")
				    outfile.write('\n')
				    outfile.write('# key: y x t hog(72) hof(90)')
				    outfile.write('\n')

				    #writes sample to file
				    for s in sample:
					    outfile.write(' '.join(s)+'\n')
				    print("File", filename_write, "created succesfully:", os.getcwd())

	    except OSError:
		    print("File", filename_read, "not found!")

    def test_functions(self):
	    feature_file = "P03_cereals_stipdet.txt"	
	    parse_file = "test_parse.txt"
	    random_sample_file = "rand_samp.txt"
	    self.parse_features(feature_file, parse_file)
	    #change k to whatever you like to test
	    self.random_sample(20, parse_file, random_sample_file)

