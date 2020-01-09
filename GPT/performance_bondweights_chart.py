#!/usr/bin/python

import sys
import pygal


def main():

    if len(sys.argv) < 3:
        print './performance_bondweights_chart.py input_filename output_filename '
        exit(1)

    input_filename = sys.argv[1]
    output_filename = sys.argv[2]

    chart_file = open(input_filename,'r')

    line_chart = pygal.Line()
    line_chart.title = 'Performance over Varying Participation Levels of Different Bond Types'
    line_chart.x_labels = chart_file.readline().strip().split(',')[1:]
    line_chart.x_title = 'Weight'
    line_chart.y_title = 'Performance'
    for line in chart_file:
        name = line.strip().split(',')[0]
        values = map(int, line.strip().split(',')[1:])
        line_chart.add(name,values)
    image_filename = output_filename + '.png'
    line_chart.render_to_png(image_filename)

    chart_file.close()


if __name__ == '__main__':
    main()