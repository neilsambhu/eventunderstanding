#!/usr/bin/python

import sys
#sys.path.append('/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/pygal')
#print sys.path
import pygal

def local_help():
    print 'usage: ./compare_approaches_varying_rank.py experiment_type experiment_name inference_versions ' \
              'ranks_separated_by_comma input_path output_path [dataset_name|degradation rank]'
    exit(1)

def main():
# 4shots_dynamic_performance_10dl_-1op_2rnk
    if len(sys.argv) < 7:
        local_help()

    experiment_type = sys.argv[1]
    experiment_name = sys.argv[2]
    inference_versions = sys.argv[3].split(',')
    rank_range = map(int, sys.argv[4].split(','))
    input_path = sys.argv[5]
    output_path = sys.argv[6]

    if experiment_type == 'synthetic':
        degradation = sys.argv[7]
        if len(sys.argv) < 9:
            print 'missing rank param -- check usage below'
            local_help()
        else:
            rank = sys.argv[8]
    else:
        dataset_name = sys.argv[7]

    approaches = {}
    average_performance = {}
    for i in range(len(inference_versions)):
        if experiment_type == 'synthetic':
            approaches[inference_versions[i]] = input_path + '/' + experiment_name + '_' + inference_versions[i] + '_performance_' + \
                                            degradation + 'dl_-1op_' + rank + 'rnk_performance_summary.txt'
        else: # real or anything else that' typed
            approaches[inference_versions[i]] = input_path + '/' + dataset_name + '_' + experiment_name + '_' + inference_versions[i] \
                                                + '_performance_summary.txt'

        average_performance[inference_versions[i]] = []

    #rank_range.insert(0,0)
    rank_range.sort()
    for version in approaches:
        file = open(approaches[version],'r')
        file.readline()
        for line in file:
            if line.strip().split(',')[0] == 'total_average':
                values = map(float, line.strip().split(',')[1:])
                average_performance['baseline'] = [values[0]] * len(rank_range)
                for i in rank_range:
                    average_performance[version].append(values[i])
        file.close()

    style = Style(
        background='white',
        plot_background='rgba(0, 0, 255, 0.03)',
        foreground='rgba(0, 0, 0, 0.8)',
        foreground_light='rgba(0, 0, 0, 0.9)',
        foreground_dark='rgba(0, 0, 0, 0.7)',
        colors=('#5DA5DA', '#FAA43A','#60BD68', '#F17CB0', '#4D4D4D', '#B2912F','#B276B2', '#DECF3F', '#F15854')
    )

    line_chart = pygal.Line(label_font_size=14, major_label_font_size=14, legend_at_bottom=True, style=style)
    line_chart.title = 'Overall Average Performance ('
    if experiment_type == 'real':
        line_chart.title += ' ' + dataset_name
    line_chart.title += ' ' + experiment_name + ')'
    line_chart.x_title = 'Rank'
    line_chart.y_title = 'Performance'
    line_chart.x_labels = map(str, map(str,rank_range))
    #line_chart.add('baseline', average_performance['baseline'])
    for version in average_performance:
        line_chart.add(version, average_performance[version])
    if experiment_type == 'synthetic':
        image_filename = output_path + '/' + experiment_name + '_' + '-'.join(inference_versions) + '_' + \
                     degradation + 'dl_-1op_' + rank + 'rnk_performance-vs-rank.png'
    else:
        image_filename = output_path + '/' + dataset_name + '_' + experiment_name + '_' + '-'.join(inference_versions) + \
                         '_performance-vs-rank.png'
    line_chart.render_to_png(image_filename)

if __name__ == '__main__':
    main()
