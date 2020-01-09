#!/usr/bin/python

import os
import sys
import glob


def change_activity_name(str):
    if str == "cereals":
        return 'cereal';
    elif str == "salat":
        return 'salad';
    return str;

def main ():
    # annt_dic = {}
    # annotation_path = '/home/students/fillipe/Breakfast_Final/lab_raw';
    # for subject_path in glob.glob(annotation_path + '/*'):
    #     for file in glob.glob(subject_path + '/*.coarse'):
    #         annt_filename = file.split('/')[-1]
    #         annt_dic[annt_filename] = []
    #         print file
    #         for line in open(file):
    #            print line
    #            # '38-199 take_cup' --> ['38_199','take_cup']
    #            content = line.split();
    #            # '38-199' --> ['38','199']
    #            frames = content[0].split('-');
    #            # 'take_cup' --> ['put','fruit2bowl']
    #            #labels = content[1].split('_');
    #            # ['38','199']+[''] --> {P03_cereal.coarse}[(38,199,'put')]
    #            annt_dic[annt_filename].append([frames[0],frames[1]])
    #            if len(content) > 1:
    #                # 'take_cup' --> ['put','fruit2bowl']
    #                labels = content[1].split('_');
    #                # ['38','199']+[''] --> {P03_cereal.coarse}[(38,199,'put')]
    #                annt_dic[annt_filename][-1].append(labels[0])
    #                if len(labels) > 1:
    #                    # 'fruit2bowl' --> ['fruit', 'bowl']
    #                    for item in labels[1].split('2'):
    #                        annt_dic[annt_filename][-1].append(item)
    #                    # {P03_cereal.coarse}[(38,199,'put','fruit','bowl')]
    # print repr(annt_dic)

    search_path = 'unit_test_features/s'+sys.argv[1]
    temporal_window_size = int(sys.argv[2])             # number of segments in a window
    granularity = int(sys.argv[3])                      # 0 for unit size or number of frames in a segment
    output_path = search_path + '/' + str(temporal_window_size) + 'seg'
    os.system('mkdir -p ' + output_path)

    i = 1
    for file in glob.glob(search_path + '/*.hofhog'):
        filename = file.split('/')[-1];
        name = filename.split('.')[0];
        parts = name.split('_');
        subject,activity,cam = parts[0],parts[1],parts[2]

        print i,subject,activity,cam
        i += 1;

        seg_collection = [];
        for seg_path in glob.glob(search_path + '/histogram/test/' + str(granularity) + '/' + activity + '/' + cam + '/' + subject + '/*'):
            segs_str = seg_path.split('/')[-1].split('_');
            print repr(segs_str);
            # get frame numbers, start -- end
            seg_collection.append([int(segs_str[0]),int(segs_str[1])]);
        seg_collection.sort();

        #seg_collection.sort(key=lambda x: x[1]);
        print repr(seg_collection);

        output_filename = subject + '_' + activity + '_' + cam
        feature_collection = []
        sequence_name = ''

        #temporal_window_size = 2
        k = 0
        while k < len(seg_collection):
            time = 0
            sequence_name += str(seg_collection[k][0])
            for item in glob.glob(search_path + '/histogram/test/' + str(granularity) + '/' + activity + '/' + cam + '/' + subject + '/' + str(seg_collection[k][0]) + '_' + str(seg_collection[k][1]) + '/*'):
                if item.endswith('.libsvm'):
                    feature_type = item.split('/')[-1].split('.')[-2]
                    feature_collection.append([feature_type, str(time), item])
                
                #write_file.write(feature_type + ' ' + time + ' ' + item + '\n')
            if k + temporal_window_size - 1 < len(seg_collection):
                sequence_name += '_' + str(seg_collection[k + temporal_window_size - 1][1])
                for j in range(k+1,k+temporal_window_size):
                    time += 1
                    for item in glob.glob(search_path + '/histogram/test/' + str(granularity) + '/' + activity + '/' + cam + '/' + subject + '/' + str(seg_collection[j][0]) + '_' + str(seg_collection[j][1]) + '/*'):
                        if item.endswith('.libsvm'):
                            feature_type = item.split('/')[-1].split('.')[-2]
                            feature_collection.append([feature_type, str(time), item])
                        #write_file.write(feature_type + ' ' + time + ' ' + item + '\n')
            else:
                sequence_name += '_' + str(seg_collection[k][1])

            # move to the next temporal window in the same video sequence
            k += temporal_window_size

            print sequence_name

            # write test feature setup file on disk
            write_file = open(output_path + '/' + output_filename + '_' + sequence_name + '.txt' ,'w')
            for item in feature_collection:
                write_file.write(' '.join(item) + '\n')
            write_file.close()

            del feature_collection[:]
            sequence_name = ''

if __name__ == '__main__':
    main();