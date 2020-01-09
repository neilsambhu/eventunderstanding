#!/usr/bin/python2.7

import sys
#sys.path.append('/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/pygal')
#print sys.path
import pygal

def main():

    if len(sys.argv) < 4:
        print 'usage: ./summarize_performance.py input_name output_name performance_indices_by_comma'
        exit(1)

    input_filename = sys.argv[1]
    output_filename = sys.argv[2]
    indices = sys.argv[3]
    performance_indices = indices.strip().split(',')

    name = input_filename.split('/')[-1].split('.')[-2]
    #performance_indices = [ 1, 3, 5 ]


    # 4shots_dynamic_performance_10dl_-1op_2rnk

    filename = input_filename
    file = open(filename)
    performance_records = {}
    for line in file:
        content = line.strip().split(',')
        sequence_name = content[0]
        if sequence_name not in performance_records:
            performance_records[sequence_name] = []

        for i in range(1,len(content)):
            performance_records[sequence_name].append(float(content[i]))
    file.close()

    average_performance_per_video = {}
    count_per_video = {}
    total_count = 0.0

    anykey = performance_records.keys()[0]
    n = len(performance_records[anykey])
    average_performance = [0.0] * n

    for sequence in performance_records:
        numbers = sequence.split('_')
        video_id = numbers[0]
        if video_id not in average_performance_per_video:
            average_performance_per_video[video_id] = [0.0] * n
            count_per_video[video_id] = 0.0

        total_count += 1.0
        count_per_video[video_id] += 1.0
        for i in range(len(performance_records[sequence])):
            average_performance_per_video[video_id][i] += performance_records[sequence][i]
            average_performance[i] += performance_records[sequence][i]

    output_file = open(output_filename,'w')
    output_file.write('videoname,baseline(support bonds,generator set),rank1(support bonds,generator set),'
                      'rank3(support bonds,generator set),rank3(support bonds,generator set)\n')


    for video in average_performance_per_video:
        val = '%.2f' % (average_performance_per_video[video][0]/count_per_video[video])
        average_performance_per_video[video][0] = float(val)
        output_file.write(video+','+val)
        for i in range(1,len(average_performance_per_video[video])):
            val = '%.2f' % (average_performance_per_video[video][i]/count_per_video[video])
            average_performance_per_video[video][i] = float(val)
            output_file.write(','+val)
        output_file.write('\n')

    val = '%.2f' % (average_performance[0]/total_count)
    output_file.write('total_average,'+val)
    for i in range(1,len(average_performance)):
        val = '%.2f' % (average_performance[i]/total_count)
        output_file.write(','+val)
    output_file.write('\n')

    output_file.close()

    chart_labels = ['baseline (SB)','baseline (GS)','rank1 (SB)','rank1 (GS)','rank2 (SB)','rank2 (GS)',
                    'rank3 (SB)','rank3 (GS)']
    x_labels = average_performance_per_video.keys()
    list_of_y_values = average_performance_per_video.values()

    bar_chart = pygal.Bar()
    bar_chart.title = 'average performance per video'
    bar_chart.x_labels = x_labels
    for i in performance_indices:
        print 'i: ',i
        index = int(i)
        y_values = [ list_of_y_values[j][k] for j in range(len(list_of_y_values))
                     for k in range(len(list_of_y_values[j])) if k == index ]
        print chart_labels[index],' ',y_values
        bar_chart.add(chart_labels[index],y_values)
    bar_chart.render_to_png(name + '_performance_summary_per_video.png')

    bar_chart = pygal.Bar()
    bar_chart.title = 'average performance'
    for i in performance_indices:
        index = int(i)
        y_values = [ average_performance[j] for j in range(len(average_performance)) if j == index ]
        print chart_labels[index],' ',y_values
        bar_chart.add(chart_labels[index],y_values)
    bar_chart.render_to_png(name + '_performance_summary.png')

    #bar_chart.render_to_file('bar_chart.svg')
    #bar_chart.render()

if __name__ == '__main__':
    main()
