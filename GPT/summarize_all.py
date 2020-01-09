#!/usr/bin/python

import sys
#sys.path.append('/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/pygal')
#print sys.path
import pygal

def local_help():
    print 'usage: ./summarize_all.py experiment_type experiments inference_versions rank_index input_path output_path ' \
              '[dataset_name|degradation rank]'
    exit(1)

def main():
# 4shots_dynamic_performance_10dl_-1op_2rnk
    if len(sys.argv) < 7:
        local_help()

    experiment_type = sys.argv[1]
    experiments = sys.argv[2].split(',')
    inference_versions = sys.argv[3].split(',')
    rank_index = int(sys.argv[4])
    input_path = sys.argv[5]
    output_path = sys.argv[6]

    if experiment_type == 'synthetic':
        degradation = sys.argv[7]
        if len(sys.argv) < 9:
            print 'missing param rank -- check usage below'
            local_help()
        else:
            rank = sys.argv[8]
    else:
        dataset_name = sys.argv[7]

    experiments.sort()

    approaches = {}
    average_performance = {}
    average_performance['baseline'] = []
    for i in range(len(experiments)):
        average_performance['baseline'].append(0.0)

    for i in range(len(inference_versions)):
        approaches[inference_versions[i]] = {}
        average_performance[inference_versions[i]] = []
        for j in range(len(experiments)):
            if experiment_type == 'synthetic':
                approaches[inference_versions[i]][experiments[j]] = input_path + '/' + experiments[j] + '_' + inference_versions[i] + '_performance_' + \
                                            degradation + 'dl_-1op_' + rank + 'rnk_performance_summary.txt'
            else:
                approaches[inference_versions[i]][experiments[j]] = input_path + '/' + dataset_name + '_' + experiments[j] + '_' \
                                                                    + inference_versions[i] + '_performance_summary.txt'
            average_performance[inference_versions[i]].append(0.0)

    for version in approaches:
        for i in range(len(experiments)):
            exp = experiments[i]
            file = open(approaches[version][exp],'r')
            file.readline()
            for line in file:
                if line.strip().split(',')[0] == 'total_average':
                    values = map(float, line.strip().split(',')[1:])
                    average_performance['baseline'][i] = values[0]
                    average_performance[version][i] = values[rank_index]
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
    #line_chart.title = 'Performance over Expanding Temporal Window Sizes'
    line_chart.x_labels = experiments
    line_chart.x_title = 'Temporal Window Size'
    line_chart.y_title = 'Performance'
    for version in average_performance:
        if version != 'baseline':
            print version,average_performance[version]
            line_chart.add(version, average_performance[version])
    line_chart.add('baseline', average_performance['baseline'])
    if experiment_type == 'synthetic':
        image_filename = output_path + '/' + '-'.join(experiments) + '_' + '-'.join(inference_versions) + '_' + \
                     degradation + 'dl_-1op_' + rank + 'rnk_performance-vs-windowsize.png'
    else:
        image_filename = output_path + '/' + dataset_name + '_' + '-'.join(experiments) + '_' + '-'.join(inference_versions) + \
                         '_performance-vs-windowsize.png'
    line_chart.render_to_png(image_filename)

if __name__ == '__main__':
    main()