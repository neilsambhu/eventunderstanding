#!/home/students/fillipe/anaconda/bin/python

import os
import random

def main():
    #approaches = ['desouza','pt','ptscsp']
    approach_name = 'ptsc'
    fold_numbers = range(1,5)
    randomization_seeds = random.sample(range(1,1000),10)

    for random_seed in randomization_seeds:
        for fold in fold_numbers:
            cmd = 'nice -n 20 ./pattern_theory.py unit_test_features/s'+str(fold)+'/s'+str(fold)+'_1seg_simul s'+str(fold)+'_1seg_simul ' + \
                approach_name+'_rs'+str(random_seed)+'_n12000_simul_ow0.5_sw2.5_ft0.1 regular bond_weights_ow0.5_sw2.5.txt 0.1 -topk 10 -ni 12000 -rs '+\
                str(random_seed)+' > out'
            os.system(cmd)

if __name__ == '__main__':
    main()
