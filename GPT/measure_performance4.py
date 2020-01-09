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
        files += glob.glob(path + '/*rank' + str(r) + '.txt')
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

def hit_counts(record, labels):
    return intersection_count(record[2], labels), len(labels)


def read_configuration_for_simultaneous_events(filename):
    file = open(filename, 'r')

    numbers = file.readline().strip().split(',')
    no_generators, no_bonds = int(numbers[0]), int(numbers[1])

    feature_generators = {}
    ontological_generators = {}

    for i in range(no_generators): # 0,4,6
        line = file.readline().strip().split(',')
        if line[5] == 'feature':
            event_name = '_'.join(line[6].split('/')[-1].split('.')[0].split('_')[0:-1])
            #print 'event_name: ',event_name
            feature_generators[line[0]] = event_name
        else:
            ontological_generators[line[0]] = line[1]

    labels_per_event = {}
    for i in range(no_bonds):
        line = file.readline().strip().split(',')
        if line[0] in feature_generators:
            event_name = feature_generators[line[0]]
            if event_name not in labels_per_event:
                labels_per_event[event_name] = []
            labels_per_event[event_name].append(ontological_generators[line[1]])
            #if time not in annt_file_per_segment:
            #    annt_file_per_segment[time] = feature_generators[line[0]][1]

    file.close()

    del feature_generators
    del ontological_generators

    frame_range_per_event = {}
    for event_name in labels_per_event:
        frame_range = event_name.split('_')
        #print 'frame range',repr(frame_range)
        frame_range_per_event[event_name] = [int(frame_range[-2]), int(frame_range[-1])]

    return labels_per_event, frame_range_per_event


def read_configuration_for_multiple_segments(filename):
    file = open(filename, 'r')

    numbers = file.readline().strip().split(',')
    no_generators, no_bonds = int(numbers[0]), int(numbers[1])

    feature_generators = {}
    ontological_generators = {}
    feature_generators_per_time = {}
    for i in range(no_generators): # 0,4,6
        line = file.readline().strip().split(',')
        if line[5] == 'feature':
            time = int(line[4])
            if time not in feature_generators_per_time: feature_generators_per_time[time] = []
            feature_generators_per_time[time].append(line[0])
            feature_generators[line[0]] = [line[4], line[6]]
        else:
            ontological_generators[line[0]] = line[1]

    labels_per_segment = {}
    annt_file_per_segment = {}
    for i in range(no_bonds):
        line = file.readline().strip().split(',')
        if line[0] in feature_generators:
            time = feature_generators[line[0]][0]
            if time not in labels_per_segment:
                labels_per_segment[time] = []
            labels_per_segment[time].append(ontological_generators[line[1]])
            if time not in annt_file_per_segment:
                annt_file_per_segment[time] = feature_generators[line[0]][1]

    file.close()

    del feature_generators
    del ontological_generators

    frame_range_per_segment = {}
    for seg in annt_file_per_segment:
        annt = annt_file_per_segment[seg].split('/')[-1].split('.')[0].split('_')
        frame_range_per_segment[seg] = [int(annt[-3]), int(annt[-2])]

    del annt_file_per_segment

    return labels_per_segment, frame_range_per_segment


def read_groundtruth_annotation(annotation_files):
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
    return video_groundtruth


def compute_performance_for_simultaneous_events(annotation_files, results_main_path, ranks=[1]):
    video_groundtruth = read_groundtruth_annotation(annotation_files)

    video_performance_scores = {}
    for result_dir in glob.glob(results_main_path + '/*'):
        # videoname format is PXX_ACTIVITY_CAMTYPE
        videoname = result_dir.split('/')[-1]

#        if videoname not in video_performance_scores: video_performance_scores[videoname] = []
        #print result_dir, repr(ranks)

        result_files = retrieve_result_files(result_dir, ranks)

        scores_per_event = {}
        for file in result_files:
            #print file
            labels_per_event, frame_range_per_event = read_configuration_for_simultaneous_events(file)
            #print repr(labels_per_event)

            for event in labels_per_event:
                if event not in scores_per_event: scores_per_event[event] = []

                labels = labels_per_event[event]
                frame_range = frame_range_per_event[event]

                subject_activity = '_'.join(event.split('_')[0:2])
                subject_activity = subject_activity.replace('salat', 'salad') if subject_activity.find('salat') >= 0 else subject_activity
                subject_activity = subject_activity.replace('cereals', 'cereal') if subject_activity.find('cereals') >= 0 else subject_activity

                for groundtruth in video_groundtruth[subject_activity]:
                    if has_overlap(groundtruth[0], groundtruth[1], frame_range[0], frame_range[1]):
                        #print 'groundtruth: ', repr(groundtruth), 'from result: ', repr(frame_range), repr(labels)
                        scores_per_event[event].append(hit_rate(groundtruth, labels))

#        best_scores_per_event = []
        for event in scores_per_event:
            if event not in video_performance_scores: video_performance_scores[event] = []

            video_performance_scores[event] = [ max( [ max(scores_per_event[event]) ] + video_performance_scores[event] ) ]
            #print 'scores at event #',event,repr(scores_per_event[event])
#            best_scores_per_event.append(max(scores_per_event[event]))

        del scores_per_event

#        if best_scores_per_event: video_performance_scores[videoname].append(float(sum(best_scores_per_event))/len(best_scores_per_event))


        print 'videoname ' + videoname

    return video_performance_scores


def compute_performance_for_multiple_segments(annotation_files, results_main_path, ranks=[1]):
    video_groundtruth = read_groundtruth_annotation(annotation_files)

    video_performance_scores = {}
    for result_dir in glob.glob(results_main_path + '/*'):
        # videoname format is PXX_ACTIVITY_CAMTYPE
        path_split = result_dir.split('/')[-1].split('_')
        subject_activity = '_'.join(path_split[:-3])
        videoname = '_'.join(path_split[:-2])
        frame_range = [int(path_split[-2]),int(path_split[-1])]

        if videoname not in video_performance_scores: video_performance_scores[videoname] = []
        print result_dir, repr(ranks)

        result_files = retrieve_result_files(result_dir, ranks)
        precision_rates = []
        scores = {}
        for file in result_files:
            print file
#            labels = retrieve_labels(file)
            rank = file.split('/')[-1].split('.')[0].split('_')[-1]
            labels_per_segment, frame_range_per_segment = read_configuration_for_multiple_segments(file)
            subject_activity = subject_activity.replace('salat', 'salad') if subject_activity.find('salat') >= 0 else subject_activity
            subject_activity = subject_activity.replace('cereals', 'cereal') if subject_activity.find('cereals') >= 0 else subject_activity
            hits = []
            counts = [] 
            for segment in labels_per_segment:
                if segment not in scores: scores[segment] = []
                labels = labels_per_segment[segment]
                frame_range = frame_range_per_segment[segment]
                for groundtruth in video_groundtruth[subject_activity]:
                    if has_overlap(groundtruth[0], groundtruth[1], frame_range[0], frame_range[1]):
                        print 'groundtruth: ', repr(groundtruth), 'from result: ', repr(frame_range), repr(labels)
                        scores[segment].append(hit_rate(groundtruth, labels))
                        #hit, count = hit_counts(groundtruth, labels)
                        #hits.append(hit)
                        #counts.append(count)
            #precision_rates.append(float(sum(hits))/sum(counts))
            #precision_rates.append(float(sum(scores))/len(scores))
            del hits
            del counts
            #del scores

        best_scores_per_segment = []
        for segment in scores:
            print 'scores at segment#',segment,repr(scores[segment])
            best_scores_per_segment.append(max(scores[segment]))

        del scores

        if best_scores_per_segment: video_performance_scores[videoname].append(float(sum(best_scores_per_segment))/len(best_scores_per_segment))

        # get max precision over the top k configurations for video
        #if precision_rates: video_performance_scores[videoname].append(max(precision_rates)) #
        #if precision_rates: video_performance_scores[videoname].append(float(sum(precision_rates))/len(precision_rates))
        print 'videoname ' + videoname

    return video_performance_scores


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

    print 'keys:'
    print repr(video_groundtruth.keys())

    video_performance_scores = {}
    for result_dir in glob.glob(results_main_path + '/*'):
        # videoname format is PXX_ACTIVITY_CAMTYPE
        path_split = result_dir.split('/')[-1].split('_')
        subject_activity = '_'.join(path_split[:-3])
        videoname = '_'.join(path_split[:-2])
        frame_range = [int(path_split[-2]), int(path_split[-1])]

        if videoname not in video_performance_scores: video_performance_scores[videoname] = []
        print result_dir, repr(ranks)

        result_files = retrieve_result_files(result_dir, ranks)
        precision_rates = []
        for file in result_files:
            print file
            labels = retrieve_labels(file)
            subject_activity = subject_activity.replace('salat','salad') if subject_activity.find('salat') >= 0 else subject_activity
            subject_activity = subject_activity.replace('cereals','cereal') if subject_activity.find('cereals') >= 0 else subject_activity
            for groundtruth in video_groundtruth[subject_activity]:
                if has_overlap(groundtruth[0], groundtruth[1], frame_range[0], frame_range[1]):
                    print 'groundtruth: ',repr(groundtruth),'from result: ',repr(frame_range),repr(labels)
                    precision_rates.append(hit_rate(groundtruth, labels))
                    #rate = hit_rate(groundtruth,labels)
                    #if rate < 1.0: rate = 0.0
                    #precision_rates.append(rate)

        if precision_rates: video_performance_scores[videoname].append(max(precision_rates)) #
        #if precision_rates: video_performance_scores[videoname].append(float(sum(precision_rates))/len(precision_rates))
        #print  + ' ' + videoname

    return video_performance_scores


def main(annotations_path, results_main_path, evaluation_type=0, ranks=[1]):
    annotation_files = [ ]
    recursive_file_search([annotations_path], annotation_files, ['coarse'])

    video_performance_rates = {}
    if evaluation_type == 1:
        video_performance_rates = compute_performance_for_multiple_segments(annotation_files, results_main_path, ranks)
    elif evaluation_type == 2:
        video_performance_rates = compute_performance_for_simultaneous_events(annotation_files, results_main_path, ranks)
    else:
        video_performance_rates = compute_performance_rates(annotation_files, results_main_path, ranks)

    for key in video_performance_rates:
        print key, repr(video_performance_rates[key])

    performance_rates = []
    for key in video_performance_rates:
        if video_performance_rates[key]: performance_rates.append(sum(video_performance_rates[key])/len(video_performance_rates[key]))

    print 'overall precision rate:'+repr(sum(performance_rates)/len(performance_rates))

if __name__ == '__main__':
    ranks = [1]
    evaluation_type = 0

    if len(sys.argv) < 3:
        print './measure_performance.py <annotations_path> <results_main_path> OPTIONS'
        print 'OPTIONS:'
        print '-m : evaluate performance for multiple-segment experiments'
        print '-s : evaluate performance for simultaneously occurring events'
        print '-r <value> : evaluation based on the top k configurations'
        exit(1)

    annotations_path = sys.argv[1]
    results_main_path = sys.argv[2]

    for arg in range(3, len(sys.argv)):
        if sys.argv[arg] == '-m':
            evaluation_type = 1
        elif sys.argv[arg] == '-s':
            evaluation_type = 2
        elif sys.argv[arg] == '-r':
            if arg+1 < len(sys.argv):
                try:
                    k = int(sys.argv[arg+1])
                except ValueError:
                    k = 1
                ranks = range(1, k+1)

    main(annotations_path, results_main_path, evaluation_type, ranks)
    #main('/home/students/fillipe/Breakfast_Final/lab_raw', '/home/students/fillipe/ICCV2015/first_results/1seg_results')
