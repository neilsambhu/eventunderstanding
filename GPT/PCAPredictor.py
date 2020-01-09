#!/usr/bin/python

from Predictor import *
import string
import os
import random
import scipy
import numpy as np
import glob
#from matplotlib.mlab import PCA
from sklearn.decomposition import PCA
from skimage.transform import resize


class PCAPredictor(Predictor):
    # Create a model_file for each predictor, named <predictor_name>_model.txt
    def __init__(self, method, feature, tanh_k, training_features_path, distance_type='cosine', mode='load'):
        super(PCAPredictor, self).__init__(method, feature, tanh_k);
        self.__distance_type = distance_type;
        self.__mode = mode;
        self.__tolerance = 0.7;
        if mode == 'load':
            self.__model = None;
            self.__projected_training_samples, self.__metadata = self.__load_training_model(training_features_path);
        else:
            print 'Creating PCAPredictor object';
            save_filepath = str(os.getpid()) + '_predictor-' + method + '_training_features';

            # Assumes that training_features_path points to a path of files generated using prepare_features(.)
            self.__model, self.__projected_training_samples, self.__metadata = \
                self.__train_model(training_features_path, save_filepath=save_filepath);

    def __avg(self,elements):
        sum = 0.0;
        n = len(elements);
        for value in elements:
            if self.__distance_type == 'cosine':
                sum += abs(float(value));
            else:
                sum += float(value);
        return (sum/n)

    def __max(self,elements,k=1):
        score = 0.0
        n = k

        if k > len(elements): n = len(elements);

        # if self.__distance_type == 'cosine':
        #     for i in range(len(elements)):
        #         elements[i] = abs(elements[i]);

        # Sorting in descending order
        #elements.sort(reverse=True);
        # Sorting in ascending order
        elements.sort();

        for i in range(n): score += elements[i];
        score = score / (1.0 * n);

        return score;

    def	__min(self,elements,k=3):
        score = 0.0;

        if k > len(elements):
            k = len(elements);

        elements.sort()

        for i in range(k): score += elements[i];
        score = score / (1.0 * k);

        return score;

        # min_index = 0
        # min_value = elements[min_index]
        # n = len(elements)
        # for i in range(1,n):
        #     if elements[i] < min_value:
        #         min_value = elements[i]
        # return min_value

    # modes: 'max', 'avg', 'mod', 'min', 'top'
    def __read_scores(self, label, filename, mode='max', k=1):
        scores = [];
        with open(filename,'r') as fp:
            for line in fp:
                data = line.strip().split(',');
                label_not_found = True;
                for value in data:
                    content = value.split(':');
                    if content[0] == label:
                        scores.append(float(content[1]));
                        label_not_found = False;
                if label_not_found == True:
                    scores.append(2.);

        return scores;

    #
    def __train_model(self, input_features_path, save_filepath = None):
        print 'Training model for features', input_features_path;

        k = 0;
        index = 0;
        training_features = [];
        training_model_metadata = [];
        file_list = glob.glob(input_features_path + '/*.spe');
        for filename in file_list:
            print filename;
            label = filename.split('/')[-1].split('.')[0];
            training_model_metadata.append([index, 0, label]);
            with open(filename, 'r') as file:
                for line in file:
                    data = line.strip().split(',');
                    training_features.append([ float(data[i]) for i in range(len(data)) ]);
                    training_model_metadata[k][1] += 1;
            index += training_model_metadata[k][1];
            k += 1;
            print training_model_metadata[k-1];

        training_data = np.array(training_features, dtype=np.float64);

        print 'Computing the PCA model...';
        print 'training data shape', training_data.shape;

        model = PCA();
        training_model = model.fit_transform(training_data);

        if save_filepath is not None:
            if os.path.isdir(save_filepath) == False:
                os.system('mkdir ' + save_filepath);

            nsamples, nfeatures = training_model.shape;
            for i in range(len(training_model_metadata)):
                index, size, label = training_model_metadata[i];
                with open(save_filepath + '/' + label + '.pca', 'w') as wfile:
                    for j in range(index,index+size):
                        wfile.write(str(training_model[j,0]));
                        for k in range(1,nfeatures):
                            wfile.write(','+str(training_model[j,k]));
                        wfile.write('\n');

        projected_training_samples = training_model;

        return model, projected_training_samples, training_model_metadata;
    
    def __load_training_model(self, training_model_path):
        print 'Loading training model', training_model_path;

        k = 0;
        index = 0;
        metadata = [];
        training_model_data = [];
        training_files = glob.glob(training_model_path + '/*.pca');
        for file in training_files:
            label = file.split('/')[-1].split('.')[0];
            metadata.append([index, 0, label]);
            with open(file,'r') as rfile:
                for line in rfile:
                    data = line.strip().split(',');
                    training_model_data.append([ float(data[i]) for i in range(len(data)) ]);
                    metadata[k][1] += 1;
            index += metadata[k][1];
            k += 1;

        print 'Finished loading the training model';

        return np.array(training_model_data, dtype=np.float64), metadata;
        
    # Load test features
    def __load_transform_test_features(self, filename):
        test_features = [];
        with open(filename, 'r') as file:
            for line in file:
                if line[0] == '#': continue;
                data = line.strip().split(',');
                nfeatures = int(data[0]);
                nsamples = int( (len(data)-1) / nfeatures );
                # Reshaping the spectrogram into an image
                spectrogram = np.reshape(np.array([float(data[i]) for i in range(1,len(data))]), (nsamples, nfeatures));
                # Resizing the spectrogram (interpolation) and flattening the feature spectrogram
                test_features.append( np.reshape( resize(spectrogram, (512, 256)), (512*256) ) );
                #test_features.append( [ float(data[i]) for i in range(len(data)) ] );
        test_data = np.array(test_features, dtype=np.float64);
        #return test_features;
        return test_data;

    def __load_test_features(self, filename):
        test_features = [];
        with open(filename, 'r') as file:
            for line in file:
                if line[0] == '#': continue;
                data = line.strip().split(',');
                # Resizing the spectrogram (interpolation) and flattening the feature spectrogram
                test_features.append( np.array( [ float(data[i]) for i in range(len(data)) ] ) );
        test_data = np.array(test_features, dtype=np.float64);
        #return test_features;
        return test_data;


    def __find_instance_label(self, target_sample_index, training_model_metadata):
        #label = 'notavailable';
        label_index = -1;
        for j in range(len(training_model_metadata)):
            index = training_model_metadata[j][0];
            size = training_model_metadata[j][1];
            if index+size > target_sample_index and target_sample_index >= index:
                label_index = j;
                #label = training_model_metadata[j][2];
        return training_model_metadata[label_index][2];

    def __project_test_data(self, test_data, model):
        X = [];
        for i in range(len(test_data)):
            X.append(test_data[i]);
        Y = model.transform(np.array(X));
        print 'Y.shape', Y.shape;
        return Y;

    def __predict_mahalanobis(self, test_data, training_model_data, training_model_metadata):
        print 'Predict for test data', test_data;
        assignment = [];
        n_test_samples, nfeatures = test_data.shape;
        n_training_samples, nfeatures = training_model_data.shape;

        means = [];
        covariances = [];

        for i in range(len(training_model_metadata)):
            index = training_model_metadata[i][0];
            size = training_model_metadata[i][1];
            X = training_model_data[index:index+size,:];
            covariances.append(np.cov(X,rowvar=0));
            print 'icov',np.linalg.inv(covariances[i]);
            means.append(np.mean(X,axis=0));

        for i in range(n_test_samples):
            assignment.append([]);
            distances = np.array( [ ( k, scipy.spatial.distance.mahalanobis(test_data[i], means[k], np.linalg.inv(covariances[k]) ) )
                                    for k in range(len(covariances)) ], dtype=[('index', int),('distance', float)] );
            distances.sort(order='distance');
            for j in range(len(distances)-1,-1,-1):
                label = training_model_metadata[distances[j][0]][2];
                score = distances[j][1];
                assignment[i].append([label,score]);

        return assignment;

    def __predict_cosine(self, test_data, training_model_data, training_model_metadata):
        print 'Predict for test data', test_data;
        assignment = [];
        n_test_samples, nfeatures = test_data.shape;
        n_training_samples, nfeatures = training_model_data.shape;
        for i in range(n_test_samples):
            assignment.append([]);

            # Compute the distance of test sample to all training samples in the training model
            distances = np.array([ ( k, scipy.spatial.distance.cosine(test_data[i],training_model_data[k]) )
                                   for k in range(n_training_samples) ], dtype=[('index', int),('distance', float)]);

            distances.sort(order='distance');

            # Find the k best different labels
            j = 1;
            k = 1;
            k_best_labels = [];
            k_label = self.__find_instance_label(distances[0][0], training_model_metadata);
            k_best_labels.append(k_label);
            assignment[i].append([k_label, distances[0][1]]);
            while j < len(distances):
                k_label = self.__find_instance_label(distances[j][0], training_model_metadata);
                if k_label not in k_best_labels:
                    k_best_labels.append(k_label);
                    assignment[i].append([k_label, distances[j][1]]);
                    k += 1;
                j += 1;

            # Freeing memory
            del k_best_labels;
            del distances;

        return assignment;

    def __predict(self, test_data, training_model_data, training_model_metadata):
        print 'Predict for test data', test_data;
        assignment = [];
        n_test_samples, nfeatures = test_data.shape;
        n_training_samples, nfeatures = training_model_data.shape;
        for i in range(n_test_samples):
            assignment.append([]);

            # Compute the distance of test sample to all training samples in the training model
            distances = np.array([ ( k, scipy.inner(test_data[i] - training_model_data[k],test_data[i] - training_model_data[k]) )
                                   for k in range(n_training_samples) ], dtype=[('index', int),('distance', float)]);

            distances.sort(order='distance');

            # Find the k best different labels
            j = 1;
            k = 1;
            k_best_labels = [];
            k_label = self.__find_instance_label(distances[0][0], training_model_metadata);
            k_best_labels.append(k_label);
            assignment[i].append([k_label, distances[0][1]]);
            while j < len(distances):
                k_label = self.__find_instance_label(distances[j][0], training_model_metadata);
                if k_label not in k_best_labels:
                    k_best_labels.append(k_label);
                    assignment[i].append([k_label, distances[j][1]]);
                    k += 1;
                j += 1;

            # Freeing memory
            del k_best_labels;
            del distances;

        return assignment;

    def __save_scores(self, assignment, output_filename):
        with open(output_filename, 'w') as fp:
            # for each sample
            for i in range(len(assignment)):
                # read the distance-based score for each label explaining that data
                fp.write(str(assignment[i][0][0])+':'+str(assignment[i][0][1]));
                for j in range(1,len(assignment[i])):
                    fp.write(','+str(assignment[i][j][0])+':'+str(assignment[i][j][1]));
                fp.write('\n');

    def baseline(self, filename):
        return self.__majority_voting_baseline(filename);

    def __majority_voting_baseline(self, filename):
        pass

    def run(self, label_name, g, mode='silent'):
        print 'Get score for', label_name;
        #model_name = label_name + g.get_name()
        
        # print 'model name: ',model_name
        if g.get_features() == None:
            print 'Return default value',(-self.__tolerance + 2.0);
            return (-self.__tolerance + 2.0);
        # elif model_name not in self.__models:
        #     return 0.0001;

        # stub (just for testing purposes):
        #	return random.uniform(0,1)

        # output_scores = g.get_name() + '_' + repr(g.get_id()) + '_' + label_name + '.scores'
        # output_scores = g.get_name() + '_' + repr(g.get_id()) + '.scores' ## for ICPR2014
        feature_filename = g.get_features().split('/')[-1]
        eventname = g.get_features().split('/')[-2]
        videoname = g.get_features().split('/')[-3]
        # output_scores = feature_filename + '_' + label_name + '.scores'
        
        # In this case, I only need to record the scores per feature file -- this is because there 
        # is only one model for all target categories/labels
        # If there was a model for each label, the filename would be sopmething like:
        #     output_scores_filename = str(os.getpid()) + '_' + label_name + '_' + feature_filename + '.scores'
        output_scores_filename = str(os.getpid()) +  '_' + videoname + '_' + eventname + '_' + feature_filename + '_' + g.get_name() + '.scores'
        print output_scores_filename;
        if os.path.isfile(output_scores_filename) == False:
            # The model is a path to the training samples projected onto the Eigenspace (w/PCA)
            #training_model_path = self.__models[model_name];
            #projected_training_samples, metadata = self.__load_training_model(training_model_path);
            
            # Test samples
            feature_file = g.get_features();
            print 'PCA predictor testing feature file', feature_file;

            X = None;
            if self.__mode == 'load':
                print 'loading test features';
                X = self.__load_test_features(feature_file);
                print 'test features shape', X.shape;
            else:
                test_data = self.__load_transform_test_features(feature_file);
                print 'test_data', test_data.shape;
                # Project test data onto PCA space
                X = self.__project_test_data(test_data, self.__model);

            # Get scores of the test data for each label
            #assignments = self.__predict(X, self.__projected_training_samples, self.__metadata);
            #assignments = self.__predict_mahalanobis(X, self.__projected_training_samples, self.__metadata);
            assignments = self.__predict_cosine(X, self.__projected_training_samples, self.__metadata);
            print 'assignment', assignments
                
            # Save the scores for each sample w.r.t training model
            self.__save_scores(assignments, output_scores_filename);
        else:
            print 'already computed';

        scores = self.__read_scores(label_name, output_scores_filename);
        print 'scores', scores;

        final_score = 0.0;
        for val in scores:
            print 'transformed score', (-self.__tolerance + val), 'score val', val;
            final_score += (-self.__tolerance + val);
        print 'final score', final_score;

        return final_score;

        # The final score is always a number in the closed range [0,2]
        # final_score = 0.0;
        # if mode == 'max':
        #     final_score = self.__max(scores,k=1);
        # elif mode == 'avg':
        #     final_score = self.__avg(scores);
        # elif mode == 'min':
        #     final_score = self.__min(scores);
        # else: # Default treatment
        #     final_score = self.__min(scores);
        #     print 'final score', final_score;
        #
        # if final_score < 0:
        #     print 'final score', final_score
        #     exit(1);

        #print 'transformed score',(-self.__tolerance + final_score), 'final score', final_score;

        #return (-self.__tolerance + final_score);
