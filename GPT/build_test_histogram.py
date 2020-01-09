#!/usr/bin/python

import os
import glob
from multiprocessing import Pool
from operator import itemgetter
import mmap
import random

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

def concat_files(ordered_file_list,output_filename='concat_result.txt'):
    with open(output_filename, 'a') as outfile:
        for fname in ordered_file_list:
            with open(fname) as infile:
                for line in infile:
                    outfile.write(line)


def prepare_fold_codebook_features(training_path, output_path):
    path_list = []
    for path in glob.glob(training_path + '/*'):
        path_list.append(path.split('/')[-1])
        
    number_of_folds = len(path_list)    
    for fold in path_list:
        fold_path = output_path + '/fold_' + fold
        print 'processing for ' + fold_path
        if os.path.isdir(fold_path) == False:
            os.system( 'mkdir ' + fold_path )
        
        if os.path.isdir(fold_path + '/codebook') == False:    
            os.system( 'mkdir ' + fold_path + '/codebook' )
        
        for training_fold in path_list:
            if training_fold != fold: 
                training_fold_path = training_path + '/' + training_fold
                for concept_path in glob.glob(training_fold_path + '/*'):
                    name = concept_path.split('/')[-1]
                    if os.path.isdir(fold_path + '/codebook/' + name) == False:
                        os.system('mkdir ' + fold_path + '/codebook/' + name)
                    for concept_file in glob.glob(concept_path + '/*'):
                        output_concept_filename = fold_path + '/codebook/' + name + '/' + concept_file.split('/')[-1] 
                        print output_concept_filename
                        concat_files([concept_file],output_concept_filename)
                        
def convert_to_numeric_vector(string_list):
    numeric_vector = []
    for i in range(len(string_list)):
        numeric_vector.append(float(string_list[i]))
    return numeric_vector

def convert_to_libsvm_format(filename,class_label,output_path=None):
    if os.path.isfile(filename+'.libsvm') == False:
        output_path = filename+'.libsvm' if output_path == None else output_path
        ifile = open(filename,'r')
        ofile = open(output_path,'w')
        for line in ifile:
            data = line.strip().split()
            ofile.write(repr(class_label))
            for i in range(len(data)):
                ofile.write(' '+repr(i+1)+':'+data[i])
            ofile.write('\n')
        ofile.close()
        ifile.close()
        return output_path
    return filename+'.libsvm'


def prepare_unit_test_features(k,input_path,output_path,code=[0,16,29,42,53]):
    frame_number_column = 6

    feature_file_list = []
    recursive_file_search([input_path], feature_file_list, ['_stipdet.txt'])
    #print 'number of feature files: ' + repr(len(feature_file_list))

    if os.path.isdir(output_path) == False:
        os.system('mkdir ' + output_path)
    if os.path.isdir(output_path + '/s' + str(k)) == False:
        os.system('mkdir ' + output_path + '/s' + str(k))

    features = []
    for feature_file in feature_file_list:
        filename = feature_file.split('/')[-1]
	#os.system('wc -l '+feature_file)
        subject = filename.split('_')[0]
        subject_id = int(subject.split('P')[1])
        if subject_id < code[k-1] or subject_id >= code[k]:
            continue

        cam = feature_file.split('/')[-2]
        activity = filename.split('_')[1]

        #count = 0
        new_filename = subject + '_' + activity + '_' + cam + '.hofhog'
        file = open(feature_file,'r')
        for line in file:
            #count += 1
            if not line.startswith('#'):
                feature_vector = convert_to_numeric_vector(line.strip().split())
                features.append(feature_vector)
                #file.write(line)
        file.close()

        #print '# of lines: '+repr(count)

        features.sort(key=itemgetter(frame_number_column))
        file = open(output_path + '/s' + str(k) + '/' + new_filename,'w')
        for feature in features:
            file.write(str(feature[0]))
            for i in range(1,len(feature)):
                file.write(' '+str(feature[i]))
            file.write('\n')
        file.close()
        del features[:]

def prepare_test_features(k,input_path,output_path,code=[0,16,29,42,53]):
    frame_number_column = 6

    feature_file_list = []
    recursive_file_search([input_path], feature_file_list, ['_stipdet.txt'])
    #print 'number of feature files: ' + repr(len(feature_file_list))

    if os.path.isdir(output_path) == False:
        os.system('mkdir ' + output_path)
    if os.path.isdir(output_path + '/s' + str(k)) == False:
        os.system('mkdir ' + output_path + '/s' + str(k))

    features = []
    for feature_file in feature_file_list:
        filename = feature_file.split('/')[-1]
	#os.system('wc -l '+feature_file)
        subject = filename.split('_')[0]
        subject_id = int(subject.split('P')[1])
        if subject_id < code[k-1] or subject_id >= code[k]:
            continue

        cam = feature_file.split('/')[-2]
        activity = filename.split('_')[1]

        #count = 0
        new_filename = subject + '_' + activity + '_' + cam + '.hofhog' 
        file = open(feature_file,'r')
        for line in file:
            #count += 1
            if not line.startswith('#'):
                feature_vector = convert_to_numeric_vector(line.strip().split())
                features.append(feature_vector)
                #file.write(line)
        file.close()

        #print '# of lines: '+repr(count)

        features.sort(key=itemgetter(frame_number_column))
        file = open(output_path + '/s' + str(k) + '/' + new_filename,'w')
        for feature in features:
            file.write(str(feature[0]))
            for i in range(1,len(feature)):
                file.write(' '+str(feature[i]))
            file.write('\n')        
        file.close()
        del features[:]

def construct_test_histograms(args): #fold_number, dimension_start, dimension, test_path='../features', output_path='..', codebook_root_path='../experiments',
    #program_path='./GMMBoVW', libsvm=False, class_label=0, temporal_window_size=0):

    test_features_path = args[0] #'../features'
    output_path = args[1] # '../features/s1'
    codebook_path = args[2] #'../features/s1/codebook'
    program_path = args[3] # './GMMBoVW'
    libsvm = args[4] # False
    class_label = args[5] # 0
    temporal_window_size = args[6] # 0
    #thread_id = args[7]

    thread_id = os.getpid()

    frame_start = 1
    tsz = temporal_window_size

    output_path += '/' + str(temporal_window_size)
    if os.path.isdir(output_path) == False:
        os.system('mkdir -p ' + output_path)

    # for each feature file
    for feature_file in glob.glob(test_features_path + '/*.hofhog'):
        # parse the file name -- it shows which concepts are represented by those features
        filename = feature_file.split('/')[-1]
        name = filename.split('.')[0]

        #frame_start = int(name.split('_')[-2])
        #frame_end = int(name.split('_')[-1])

        frame_start = 1

        names = name.split('_')
        subject = names[0]
        activity = names[1]
        cam = names[2]

        tmp_output_path = output_path + '/' + activity + '/' + cam + '/' + subject
        os.system('mkdir -p ' + output_path + '/' + activity + '/' + cam + '/' + subject)

        print 'processing feature file "' + filename + '"'

        concepts = []
        for i in range(2,len(names)-2):
            concepts.append(names[i])
#        print 'concepts: ' + repr(concepts)

        #os.system(output_path + '/' + )
        # if no window size is set, construct histogram for the whole video
        window_end = frame_start + temporal_window_size - 1
        if temporal_window_size < 1:
            # construct histogram for motion features
            name = feature_file.split('/')[-1].split('.')[0]

            interval_start = name.split('_')[-2]
            interval_end = name.split('_')[-1]
            os.system('mkdir -p ' + tmp_output_path + '/' + interval_start + '_' + interval_end)
            tmp_output_path += '/' + interval_start + '_' + interval_end

            feature_start = 75
            feature_dimension = 90
            output_filename = tmp_output_path + '/' + name + '_0.hof'
            print 'create file ' + output_filename
            build_histogram(feature_start, feature_dimension, output_filename, concepts, codebook_path + '/actions',
                            feature_file, program_path, libsvm, class_label)

            # find number of objects
            parts = name.split('_')
            object_count = len(parts) - 6
            
            feature_start = 3
            feature_dimension = 72
            for i in range(1,object_count+1):
                output_filename = tmp_output_path + '/' + name + '_' + str(i) + '.hog'
                print 'create file ' + output_filename
                build_histogram(feature_start, feature_dimension, output_filename, concepts, codebook_path + '/objects',
                            feature_file, program_path, libsvm, class_label)

            # the code inside this if condition is not useful yet... I have to change it
        else: # otherwise, construct histograms for smaller temporal windows
            features = []
            file = open(feature_file,'r')
            for line in file:
                feature_vector = convert_to_numeric_vector(line.strip().split())
                features.append(feature_vector)
            file.close()

            # sort feature vectors by frame number
            features.sort(key=itemgetter(6))

            # set end of temporal window
            window_end = frame_start + tsz - 1 #if frame_start + tsz - 1 <= frame_end else len(features)-1

            # read each feature
            filename = str(thread_id) + '_data.txt'
            file = open(filename,'w')
            i = 0
#            print 'total features',len(features)
            while i < len(features) + 1:
                # if feature vector falls into the current temporal window interval
                if i < len(features) and features[i][6] <= window_end:
                    # store feature vector on feature file in construction
                    file.write(repr(features[i][0]))
                    for j in range(1,len(features[i])):
                        file.write(' ' + repr(features[i][j]))
                    file.write('\n')
                else:
#                    print 'features',i,'frame start:',frame_start,'frame end:',window_end
                    # close the newly created file containing features in the current temporal window
                    file.close()

                    os.system('mkdir -p ' + tmp_output_path + '/' + str(frame_start) + '_' + str(window_end))

                    # compute histogram with the features in the current temporal window
                    feature_start = 75
                    feature_dimension = 90
                    output_filename = tmp_output_path + '/' + str(frame_start) + '_' + str(window_end) + '/0.hof'
                    build_histogram(feature_start, feature_dimension, output_filename, concepts,
                                    codebook_path + '/actions', filename, program_path, libsvm, class_label)

                    feature_start = 3
                    feature_dimension = 72
                    for j in range(1,3):
                        output_filename = tmp_output_path + '/' + str(frame_start) + '_' + str(window_end) + '/' + str(j) + '.hog'
                        build_histogram(feature_start, feature_dimension, output_filename, concepts,
                                        codebook_path + '/objects', filename, program_path, libsvm, class_label)

                    # keep pointing to this feature vector so it is stored in the next feature file for the next temporal window
                    i = i - 1 if i < len(features) else i

                    frame_start = window_end + 1
                    # set the end of temporal window
                    window_end += temporal_window_size # if len(features) - window_end < temporal_window_size else len(features)-1

                    # open the new file to store feature from the next temporal window
                    file = open(filename,'w')
                i += 1
            del features[:]
            file.close()

def prepare_features_for_codebook_building(features_path='../features',output_path='../experiments',fold_number=1):
    # set feature folder name
    fold_path = features_path + '/s' + repr(fold_number)
    if os.path.isdir(output_path + '/s' + repr(fold_number)) == False:
        os.system('mkdir ' + output_path + '/s' + repr(fold_number))
    output_path += '/s' + repr(fold_number)

    if os.path.isdir(output_path + '/actions') == False:
        os.system('mkdir ' + output_path + '/actions')

    if os.path.isdir(output_path + '/objects') == False:
        os.system('mkdir ' + output_path + '/objects')

    # for each feature file in the folder containing feature files
    for feature_file in glob.glob(fold_path + '/*.hofhog'):
        # extract filename
        filename = feature_file.split('/')[-1]
        # extract activity and objects names
        tag_names = filename.split('.')[0].split('_')
        # get action name
        activity = tag_names[2]
        # read prepositions if they exist to compliment the action's name
        index = 3
        while tag_names[index] in ['in','out','up','down','on','into','onto']:
            activity += '_' + tag_names[index]
            index += 1
        # create/update file containing features for activity y
        output_filename = output_path + '/actions.hofhog'
        outfile = open(output_filename)
        file = open(filename)
        for line in file:
            outfile.write(line)
        file.close()

def assemble_training_histograms(args):
    feature_file = args[0]
    temporal_window_size = args[1]
    output_path = args[2]
    codebook_path = args[3]
    program_path = args[4]
    libsvm = args[5]
    class_label = args[6]
    thread_id = args[7]

    # parse the file name -- it shows which concepts are represented by those features
    filename = feature_file.split('/')[-1]
    name = filename.split('.')[0]
    frame_start = int(name.split('_')[-2])
    frame_end = int(name.split('_')[-1])
    names = name.split('_')

    #count += (frame_end - frame_start + 1)/temporal_window_size
    #count = count + 1 if (frame_end - frame_start + 1)%temporal_window_size > 0 else count
    #print 'Processing ' + feature_file + ' Count ' + str(count)

    print filename,frame_start,frame_end

    concepts = []
    for j in range(2,len(names)-2):
        concepts.append(names[j])
    #print 'concepts: ' + repr(concepts)

    # if no window size is set, construct histogram for the whole video
    if temporal_window_size < 1:
        build_action_object_histogram(output_path, concepts, codebook_path, feature_file, program_path,libsvm, class_label)
    else: # otherwise, construct histograms for smaller temporal windows
        features = []
        file = open(feature_file,'r')
        for line in file:
            feature_vector = convert_to_numeric_vector(line.strip().split())
            features.append(feature_vector)
        file.close()

        # sort feature vectors by frame number
        features.sort(key=itemgetter(2))

        # set end of temporal window
        window_end = frame_start + temporal_window_size - 1 if frame_start + temporal_window_size - 1 <= frame_end else frame_end

        # read each feature
        window_count = 0
        filename = str(thread_id) + '_data.txt'
        file = open(filename,'w')
        i = 0
        while i < len(features)+1:
            # if feature vector falls into the current temporal window interval
            if i < len(features) and features[i][2] <= window_end:
                # store feature vector on feature file in construction
                file.write(repr(features[i][0]))
                for j in range(1,len(features[i])):
                    file.write(' ' + repr(features[i][j]))
                file.write('\n')
                #print 'window_end',window_end,'frame number',features[i][2]
            else:
                window_count += 1
                print 'window_count:',window_count

                # close the newly created file containing features in the current temporal window
                file.close()

                # compute histogram with the features in the current temporal window
                build_action_object_histogram(output_path, concepts, codebook_path, filename, program_path, libsvm, class_label)

                # keep pointing to this feature vector so it is stored in the next feature file for the next temporal window
                i = i - 1 if i < len(features) else i

                # set the end of temporal window
                window_end = window_end + temporal_window_size if frame_end <= window_end + temporal_window_size else frame_end

                # open the new file to store feature from the next temporal window
                file = open(filename,'w')
            i += 1
        del features[:]
        file.close()

def construct_training_histograms(args):
    fold = args[0] # 1
    training_path = args[1] #'../features'
    output_path = args[2] # '../features/s1'
    codebook_path = args[3] #'../features'
    program_path = args[4] # './GMMBoVW'
    libsvm = args[5] # False
    class_label = args[6] # 0
    temporal_window_size = args[7] # 0 
    number_of_folds = args[8]
    thread_id = args[9]

    thread_id = os.getpid();

    tsz = temporal_window_size

    if os.path.isdir(output_path + '/histogram/train/' + str(tsz)) == False:
        os.system( 'mkdir -p ' + output_path + '/histogram/train/' + str(tsz))
    output_path += '/histogram/train/' + str(tsz)

#    pool = Pool(16)

    #count = 0 # debug variable
    #window_count = 0
    tasks = []
    for training_fold_index in range(1, number_of_folds+1):
        if training_fold_index != fold:
            training_fold_path = training_path + '/s' + str(training_fold_index)
            # for each feature file
            for feature_file in glob.glob(training_fold_path + '/*.hofhog'):
                assemble_training_histograms( ( feature_file, temporal_window_size, output_path, codebook_path, program_path, libsvm, class_label, thread_id))
                #tasks.append( ( feature_file, temporal_window_size, output_path, codebook_path,
                #                              program_path, libsvm, class_label ) )
                # #count += 1
                # #                print 'Processing ' + feature_file
                #
                # # parse the file name -- it shows which concepts are represented by those features
                # filename = feature_file.split('/')[-1]
                # name = filename.split('.')[0]
                # frame_start = int(name.split('_')[-2])
                # frame_end = int(name.split('_')[-1])
                # names = name.split('_')
                # #print 'processing feature file "' + filename + '"'
                #
                # #count += (frame_end - frame_start + 1)/temporal_window_size
                # #count = count + 1 if (frame_end - frame_start + 1)%temporal_window_size > 0 else count
                # #print 'Processing ' + feature_file + ' Count ' + str(count)
                #
                # concepts = []
                # for j in range(2,len(names)-2):
                #     concepts.append(names[j])
                # #print 'concepts: ' + repr(concepts)
                #
                # # if no window size is set, construct histogram for the whole video
                # if temporal_window_size < 1:
                #     build_action_object_histogram(output_path, concepts, codebook_path, feature_file, program_path,libsvm, class_label)
                # else: # otherwise, construct histograms for smaller temporal windows
                #     features = []
                #     file = open(feature_file,'r')
                #     for line in file:
                #         feature_vector = convert_to_numeric_vector(line.strip().split())
                #         features.append(feature_vector)
                #     file.close()
                #
                #     # sort feature vectors by frame number
                #     features.sort(key=itemgetter(2))
                #
                #     # set end of temporal window
                #     window_end = frame_start + tsz - 1 if frame_start + tsz - 1 <= frame_end else frame_end
                #
                #     # read each feature
                #     filename = 'data.txt'
                #     file = open(filename,'w')
                #     i = 0
                #     #               print 'features: ',len(features)
                #     while i < len(features):
                #         # if feature vector falls into the current temporal window interval
                #         #print 'window_end',window_end,'frame number',features[i][2]
                #         if i < len(features) and features[i][2] <= window_end:
                #             # store feature vector on feature file in construction
                #             file.write(repr(features[i][0]))
                #             for j in range(1,len(features[i])):
                #                 file.write(' ' + repr(features[i][j]))
                #             file.write('\n')
                #         else:
                #             #                        window_count += 1
                #             # close the newly created file containing features in the current temporal window
                #             file.close()
                #
                #             # compute histogram with the features in the current temporal window
                #             build_action_object_histogram(output_path, concepts, codebook_path, filename, program_path, libsvm, class_label)
                #
                #             # keep pointing to this feature vector so it is stored in the next feature file for the next temporal window
                #             i -= 1
                #
                #             # set the end of temporal window
                #             window_end = window_end + temporal_window_size if frame_end <= window_end + temporal_window_size else frame_end
                #
                #             # open the new file to store feature from the next temporal window
                #             file = open(filename,'w')
                #         i += 1
                #     del features[:]
                #     file.close()
#    pool.map(assemble_training_histograms, tasks)

# count number of lines in a file, one of the fastest way I found
def count_lines(filename):
    return sum(1 for line in open(filename))

#    f = open(filename, "r+")
#    buf = mmap.mmap(f.fileno(), 0)
#    lines = 0
#    readline = buf.readline
#    while readline():
#        lines += 1
#    return lines

def find_feature_files(train_path,fold_number=-1,total_number=-1):
    video_feature_files = glob.glob(train_path + '/*.hofhog')
    if fold_number > 0:
        video_feature_files = []
        for i in range(1,total_number):
            if i != fold_number:
                video_feature_files += glob.glob(train_path + '/s' + str(fold_number) + '/*.hofhog')
    return video_feature_files

# input filename, pointer to output file, array containing the indices of the selected lines
def write_selected_lines(infilename,outfile,selected_lines):
    # search over all lines in the file
    count = 0
    infile = open(infilename)
    for line in infile:
        # if the line is among the selected ones
        if count in selected_lines:
            # record it on the sampling file
            outfile.write(line.strip()+'\n')
            selected_lines.remove(count)

        # break the loop if all samples having been selected
        if not selected_lines:
            break

        count += 1

def sample_lines_from_files(sampling_size,n_files,outfile,file_list=[]):
    n_samples = sampling_size / n_files
    n_remaining_samples = sampling_size
    for filename in file_list:
        n_lines = count_lines(filename)

        # selected the lines in the file to sever as samples
        #if n_samples > n_lines:
        #   n_samples = n_lines
        n_samples = n_samples if n_samples <= n_lines else n_lines
        selected_lines = random.sample(range(0,n_lines),n_samples)    

        # write selected lines on file
        write_selected_lines(filename, outfile, selected_lines)

        # update the number of samples to be sampled in the next iteration
        n_remaining_samples -= n_samples
        n_samples = sampling_size / n_files
        if n_remaining_samples < n_samples:
            n_samples = n_remaining_samples

    return n_remaining_samples

# sample feature points to be used for learning a visual codebook
def feature_sampling_for_codebook_building(args):
    if len(args) < 1:
        output_path = '../features/s1/codebook_training_features.txt'
        train_path = '../features'
        sampling_size = 100000
        fold_number = 1
        total_number = 4

    output_path = args[0]
    train_path = args[1]
    sampling_size = args[2]
    fold_number = args[3]
    total_number = args[4]

    # get training file's paths
    video_feature_files = find_feature_files(train_path, fold_number, total_number)

    n_files = len(video_feature_files)
#    print 'total number of points: ',n_files
    sampling_feature_file = open(output_path,'w')

    n_remaining_samples = sample_lines_from_files(sampling_size, n_files, sampling_feature_file, video_feature_files) 
    while n_remaining_samples > 0:
        file_number = random.randint(0,n_files)
        n_remaining_samples = sample_lines_from_files(n_remaining_samples, 1, sampling_feature_file, [ video_feature_files[file_number] ])

    sampling_feature_file.close() 


def build_histogram(dimension_start, dimension, output_filename, concepts, codebook_path, feature_filename,
                    program_path, libsvm, class_label):
    # setting histogram building options
    cmd_options = '--build_histograms '
    cmd_options += ' --codebook_path ' + codebook_path
    cmd_options += ' --dimension ' + str(dimension)
    cmd_options += ' --start ' + str(dimension_start)
    cmd_options += ' --input_file ' + feature_filename
    cmd_options += ' --output_file ' + output_filename
    if libsvm == True:
        cmd_options += ' --libsvm ' + str(class_label)

    # execute program to compute histograms    
    print 'Executing ' + program_path + ' ' + cmd_options
    os.system(program_path + ' ' + cmd_options)


def build_action_object_histogram(output_path, concepts, codebook_path, filename, program_path, libsvm, class_label):
    
    os.system('mkdir -p '+output_path+'/actions')
    os.system('mkdir -p '+output_path+'/objects')

    # setting processing params
    hof_start = 75
    hof_dimension = 90
    output_filename = output_path + '/actions/' + concepts[0]
    c_index = 1
    while c_index < len(concepts) and concepts[c_index] in ['in','out','up','down','on','into','onto']:
        output_filename += '_' + concepts[c_index]
        c_index += 1
    output_filename += '.hist'

    cmd_options = '--build_histograms '
    cmd_options += ' --codebook_path ' + codebook_path + '/actions'
    cmd_options += ' --dimension ' + str(hof_dimension)
    cmd_options += ' --start ' + str(hof_start)
    cmd_options += ' --input_file ' + filename
    cmd_options += ' --output_file ' + output_filename
    if libsvm == True:
        cmd_options += ' --libsvm ' + str(class_label)

    # execute program to compute histograms    
    print 'Executing ' + program_path + ' ' + cmd_options
    os.system(program_path + ' ' + cmd_options)

    for j in range(c_index,len(concepts)):
        # feature parse param setting
        hog_start = 3
        hog_dimension = 72

        # construct output filename
        output_filename = output_path + '/objects/' + concepts[j] + '.hist'

        # setting command options of the program
        cmd_options = '--build_histograms '
        cmd_options += ' --codebook_path ' + codebook_path + '/objects'
        cmd_options += ' --dimension ' + str(hog_dimension)
        cmd_options += ' --start ' + str(hog_start)
        cmd_options += ' --input_file ' + filename
        cmd_options += ' --output_file ' + output_filename
        if libsvm == True:
            cmd_options += ' --libsvm ' + str(class_label)

        # execute program to assemble histograms
        print 'Executing ' + program_path + ' ' + cmd_options
        os.system(program_path + ' ' + cmd_options)

def build_codebooks(root_path='../experiments', program_path='./GMMBoVW'):
    # setting command options of the program
    hog_start = 3
    hog_dimension = 72
    hof_start = 75
    hof_dimension = 90
    actions_codebook_size = 400
    objects_codebook_size = 600
    
    for fold_path in glob.glob(root_path + '/*'):
        data_file = fold_path + '/codebook/actions/actions.hof'
        for file in glob.glob(fold_path + '/codebook/actions/*.hofhog'):
            concat_files([file],data_file)
        
        cmd_options = '--build_codebook ' + fold_path + '/codebook/actions'
        cmd_options += ' --codebook_size ' + str(actions_codebook_size)
        cmd_options += ' --dimension ' + str(hof_dimension)
        cmd_options += ' --start ' + str(hof_start)
        cmd_options += ' --input_file ' + data_file
        
        # execute program to assemble histograms    
        print program_path + ' ' + cmd_options
        os.system(program_path + ' ' + cmd_options)
        
        data_file = fold_path + '/codebook/objects/objects.hog'
        for file in glob.glob(fold_path + '/codebook/objects/*.hofhog'):
            concat_files([file],data_file)
            
        cmd_options = '--build_codebook ' + fold_path + '/codebook/objects'
        cmd_options += ' --codebook_size ' + str(objects_codebook_size)
        cmd_options += ' --dimension ' + str(hog_dimension)
        cmd_options += ' --start ' + str(hog_start)
        cmd_options += ' --input_file ' + data_file  
        
        # execute program to assemble histograms
        print program_path + ' ' + cmd_options    
        os.system(program_path + ' ' + cmd_options)     

def codebook_building(fold_number, actions_codebook_size=50, objects_codebook_size=50, root_path='../features', program_path='./GMMBoVW'):
    # setting command options of the program
    hog_start = 3
    hog_dimension = 72
    hof_start = 75
    hof_dimension = 90

    fold_path = root_path + '/s' + str(fold_number)
    data_file = fold_path + '/codebook_training_features.txt'

    if os.path.isdir(fold_path + '/codebook') == False:
	os.system('mkdir ' + fold_path + '/codebook')

    if os.path.isdir(fold_path + '/codebook/actions') == False:
	os.system('mkdir ' + fold_path + '/codebook/actions')

    if os.path.isdir(fold_path + '/codebook/objects') == False:
	os.system('mkdir ' + fold_path + '/codebook/objects')

    cmd_options = '--build_codebook ' + fold_path + '/codebook/actions'
    cmd_options += ' --codebook_size ' + str(actions_codebook_size)
    cmd_options += ' --dimension ' + str(hof_dimension)
    cmd_options += ' --start ' + str(hof_start)
    cmd_options += ' --input_file ' + data_file

    # execute program to assemble histograms
    print program_path + ' ' + cmd_options
    os.system(program_path + ' ' + cmd_options)

    cmd_options = '--build_codebook ' + fold_path + '/codebook/objects'
    cmd_options += ' --codebook_size ' + str(objects_codebook_size)
    cmd_options += ' --dimension ' + str(hog_dimension)
    cmd_options += ' --start ' + str(hog_start)
    cmd_options += ' --input_file ' + data_file

    # execute program to assemble histograms
    print program_path + ' ' + cmd_options
    os.system(program_path + ' ' + cmd_options)

def main():
    #construct_test_histograms(4)

    #prepare_test_features(1,'../BreakfastII_15fps_qvga_sync','../test_features')

    #construct_training_histograms()

    #build_codebooks()



    # exit(1)
 
    features_path = '../features'
    sampling_size = 100000
    n_folds = 4

    pool = Pool(10)

    tasks = []
    window_size = 0

#    i = 1
#    construct_test_histograms(('../test_features/s'+str(i),'../test_features/s'+str(i)+'/histogram/test','../features/s'+str(i)+'/codebook','./GMMBoVW',False,0,window_size,4,os.getpid()))
    #exit(1)


    for i in range(1, n_folds+1):
        tasks.append(('unit_test_features/s'+str(i),'unit_test_features/s'+str(i)+'/histogram/test',
                      'train_features/s'+str(i)+'/codebook', './GMMBoVW', False, 0, window_size)) #, 4, os.getpid()))
    pool.map(construct_test_histograms, tasks)

    # converting test histograms into .libsvm format
    input_path_list = []
    feature_file_list = []
    for i in range(1,5):
        input_path_list.append('unit_test_features/s'+str(i)+'/histogram/test')
    recursive_file_search(input_path_list, feature_file_list, ['hog','hof'])
    for file in feature_file_list:
        print 'CONVERTING '+file
        convert_to_libsvm_format(file,1)

    # sample features to construct the codebooks
#    tasks = []
#    for i in range(1, n_folds+1):
#        tasks.append( ('../features/s'+str(i)+'/codebook_training_features.txt', features_path, sampling_size, i, n_folds) )
#    pool.map(feature_sampling_for_codebook_building, tasks)

    # construct actions and objects codebooks
#    tasks = []
#    for i in range(1, n_folds+1):
#        tasks.append(i)
#    pool.map(codebook_building, tasks)

    # construct training histograms
#    tasks = []
#    window_size = 0
#    while window_size <= 100:
#        for i in range(1, n_folds+1):
#            #construct_training_histograms((i,'../features','../features/s'+str(i),'../features/s'+str(i)+'/codebook','./GMMBoVW',False,0,window_size,4))
#            tasks.append((i,'../features','../features/s'+str(i),'../features/s'+str(i)+'/codebook','./GMMBoVW',False,0,window_size,4,os.getpid()))
#        window_size += 50
#    pool.map(construct_training_histograms, tasks)

    #codebook_building()

    #output_path = '/Volumes/FDMS_PHD_1/experiments'
    #training_path = '/Volumes/FDMS_PHD_1/codebook_features'
    #prepare_fold_codebook_features(training_path, output_path)     
    
if __name__ == "__main__":
    main()

