#!/apps/python/2.7.5/bin/python2.7

import re
import os
import sys
import glob


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
                    if item.endswith(extension):
                        file_list.append(item)

    return recursive_file_search(item_list,file_list,file_extension)


def retrieve_labels(config_file):
    labels = []
    file = open(config_file, 'r')
    line = file.readline().strip().split(',')
    number_of_generators = int(line[0])
    for i in range(number_of_generators):
        line = file.readline()
        content = line.strip().split(',')
        if content[3] in ['level2', 'level3']:
            labels.append(content[1])
        del content
    file.close()
    return labels


def retrieve_result_files(path, ranks=[1]):
    files = []
    for r in ranks:
        files += glob.glob(path + '/*rank' + str(   r) + '.txt')
    return files


def parse_labels(content):
    # parse label names
    labels = []
    regex_pattern = '|'.join(map(re.escape, ['_','2']))
    concepts = re.split(regex_pattern, content)

    action_name = concepts[0]
    index = 1
    if len(concepts) > 1:
        #action_name = action_name + concepts[index] 
        if concepts[index] in ['in','out','up','down']:
            action_name = action_name + concepts[index]
            index += 1
    action_name += '-a'
    labels.append(action_name)
    for i in range(index,len(concepts)):
        labels.append(concepts[i]+'-o')

    return labels


def intersection_count(lista, listb):
    return len(list(set(lista) & set(listb)))


def has_overlap(a, b, c, d):
    return c < b and d > a  #return (a <= c and c < b) or (a < d and d <= b)


# def overlap_amount(a, b, c, d):
#     if a <= c and c < b:
#         return min((1.0*min(b,d)-c)/(d-c), 1.0)
#     elif a < d and d <= b:
#         return min()
#     elif c < a and d
#     else:
#         return 0.0


def hit_rate(record, labels):
    return float(intersection_count(record[2], labels))/len(labels)


def compute_performance_rates(annotation_files, results_main_path, ranks=[1]):
    video_groundtruth = {}
    for file in annotation_files:
        # format is PXX_ACTIVITY.coarse
        subject_activity = file.split('/')[-1].split('.')[0]
        video_groundtruth[subject_activity] = []
        for line in open(file, 'r'):
            line_content = line.strip().split()
            frames = line_content[0].split('-')
            labels = parse_labels(line_content[1])
            video_groundtruth[subject_activity].append((int(frames[0]), int(frames[1]), labels))

    #print 'keys:'
    #print repr(video_groundtruth.keys())

    video_performance_scores = {}
    for result_dir in glob.glob(results_main_path + '/*'):
        # videoname format is PXX_ACTIVITY_CAMTYPE
        path_split = result_dir.split('/')[-1].split('_')
        subject_activity = '_'.join(path_split[:-3])
        videoname = '_'.join(path_split[:-2])
        frame_range = [int(path_split[-2]), int(path_split[-1])]

        if 'SIL' in videoname: continue    

        if videoname not in video_performance_scores: video_performance_scores[videoname] = []
        #print result_dir, repr(ranks)

        result_files = retrieve_result_files(result_dir, ranks)
        precision_rates = []
        for file in result_files:
            print file
            labels = retrieve_labels(file)
            subject_activity = subject_activity.replace('salat','salad') if subject_activity.find('salat') >= 0 else subject_activity
            subject_activity = subject_activity.replace('cereals','cereal') if subject_activity.find('cereals') >= 0 else subject_activity
            for groundtruth in video_groundtruth[subject_activity]:
                if has_overlap(groundtruth[0], groundtruth[1], frame_range[0], frame_range[1]):
                    #print 'groundtruth: ',repr(groundtruth),'from result: ',repr(frame_range),repr(labels),' ',repr(hit_rate(groundtruth,labels))
                    precision_rates.append(hit_rate(groundtruth, labels))
                    #rate = hit_rate(groundtruth,labels)
                    #if rate < 1.0: rate = 0.0
                    #precision_rates.append(rate)

        if precision_rates: video_performance_scores[videoname].append(float(sum(precision_rates))/len(precision_rates))
        #print  + ' ' + videoname

    return video_performance_scores


def main(annotations_path, results_main_path):
    annotation_files = [ ]
    recursive_file_search([annotations_path], annotation_files, ['coarse'])
    video_performance_rates = compute_performance_rates(annotation_files, results_main_path, range(1,11))
    #for key in video_performance_rates:
    #    print key, repr(video_performance_rates[key])

    performance_rates = []
    for key in video_performance_rates:
        if video_performance_rates[key]: performance_rates.append(sum(video_performance_rates[key])/len(video_performance_rates[key]))
    print 'overall precision rate:'+repr(sum(performance_rates)/len(performance_rates))

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print './measure_performance.py <annotations_path> <results_main_path>'
        exit(1)
    annotations_path = sys.argv[1]
    results_main_path = sys.argv[2]
    main(annotations_path, results_main_path)
    #main('/home/students/fillipe/Breakfast_Final/lab_raw', '/home/students/fillipe/ICCV2015/first_results/1seg_results')
