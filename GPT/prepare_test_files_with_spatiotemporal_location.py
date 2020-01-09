#!/home/students/fillipe/anaconda/bin/python

import os
import sys
import glob

def get_spatiotemporal_range(feature_file):
    x = []
    y = []
    t = []
    f = open(feature_file, 'r')
    for line in f:
        location = line.strip().split()[0:3]
        y.append(int(location[0]))
        x.append(int(location[1]))
        t.append(int(location[2]))
    f.close()
    return [min(y), max(y)], [min(x),max(x)], [min(t),max(t)]

def main(test_input_files, features_root_path, output_path):
    test_files = glob.glob(test_input_files + '/*.txt')
    for file in test_files:
        fp = open(file)
        line = fp.readline()
        fp.close()
        content = line.split('/')[-1].split('.')[0].split('_')
        if len(line) < 1: continue
        print file, line
        feature_file = features_root_path + '/' + '_'.join(content[0:-1]) + '.hofhog'
        x_range, y_range, t_range = get_spatiotemporal_range(feature_file)
        test_filename = file.split('/')[-1]
        output_filename = output_path + '/' + test_filename
        ofile = open(output_filename, 'w')
        ifile = open(file, 'r')
        for line in ifile:
            ofile.write(line.strip() + ' ' + str(y_range[0]) + ' ' + str(y_range[1]) + ' '
                        + str(x_range[0]) + ' ' + str(x_range[1]) + ' '
                        + str(t_range[0]) + ' ' + str(t_range[1]) + '\n')
        ifile.close()
        ofile.close()

if __name__ == '__main__':
    test_input_files = sys.argv[1]
    features_root_path = sys.argv[2]
    output_path = sys.argv[3]
    if os.path.isdir(output_path) == False:
        os.system('mkdir -p ' + output_path)
    main(test_input_files, features_root_path, output_path)
