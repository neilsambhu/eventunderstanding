#!/home/students/fillipe/anaconda/bin/python

import os
import sys
import glob
import random

def main(input_test_files_path, output_path, shift_amount_in_pixels):
    input_test_files = glob.glob(input_test_files_path + '/*.txt')
    for test_file in input_test_files:
        second_test_file = random.sample(input_test_files, 1)[0]
        while second_test_file == test_file:
            second_test_file = random.sample(input_test_files, 1)[0]
        test_filename = test_file.split('/')[-1].split('.')[0] + '-' + second_test_file.split('/')[-1]
        tfile = open(test_file, 'r')
        ofile = open(output_path + '/' + test_filename, 'w')
        for line in tfile: ofile.write(line)
        tfile.close()
        tfile = open(second_test_file, 'r')
        for line in tfile:
            content = line.strip().split()
            spatial_info = content[-6:-4]
            for i in range(len(spatial_info)): spatial_info[i] = str(int(spatial_info[i]) + shift_amount_in_pixels)
            ofile.write(' '.join(content[0:-6]) + ' ' + ' '.join(spatial_info) +
                        ' ' + ' '.join(content[-4:len(content)]) + '\n')
        tfile.close()
        ofile.close()

if __name__ == '__main__':
    # example: ./prepare_test_files_for_simul_events.py unit_test_features/s1/s1_1seg_location unit_test_features/s1/s1_1seg_simul 10 > out &
    input_test_files_path = sys.argv[1]
    output_path = sys.argv[2]
    os.system('mkdir -p ' + output_path)
    shift_amount_in_pixels = int(sys.argv[3])
    main(input_test_files_path, output_path, shift_amount_in_pixels)
