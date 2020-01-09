#!/home/students/fillipe/anaconda/bin/python

import os
import matplotlib.pyplot as plt


def parse_performance_rate(performance_file):
    line = '0.0'
    for line in open(performance_file,'r'): pass
    return float(line.strip().split(':')[-1])


def compute_rank_performance(root_path='/home/students/fillipe/ICCV2015/SIL_icpr_location_n12000_simul_ow0.5_sw2.5_ft0.1',
         script_path='measure_performance5.py', annotations_path='/home/students/fillipe/Breakfast_Final/lab_raw',
         ranks=range(1,11), folds=range(1,5)):

    performance_per_rank = {}

    for r in ranks:
        for f in folds:
            performance_file = 'output_performance.txt'
            os.system('./'+script_path+' '+annotations_path+' '+root_path+'/s'+str(f)+
                      '_1seg_simul_results -s -r '+str(r)+' > '+performance_file)
            if r not in performance_per_rank: performance_per_rank[r] = []
            performance_per_rank[r].append(parse_performance_rate(performance_file))

    performances = []
    for r in performance_per_rank:
        performances.append(float(sum(performance_per_rank[r]))/len(performance_per_rank[r]))

    del performance_per_rank

    return performances


def plot_save_graphs(approach_names=[],x_values=[],y_values=[]):
    line_style = ['-', '--', '-.']
    for i in range(len(approach_names)):
        #approach = approach_names[i]
        plt.plot(x_values[i], y_values[i], line_style[i])

    plt.xlabel(r'\textbf{top k best interpretations}')
    plt.ylabel(r'\textit{} Performance',fontsize=16)

    plt.savefig('top_k_performance')


def main():
    script_path='measure_performance_no_SIL.py'
    root_path = '/home/students/fillipe/ICCV2015'
    approaches = ['ICPR', 'PT+SC', 'PT+SC+SP']
    approaches_results_pathname = ['SIL_icpr_n12000_simul_ow0.5_sw2.5_ft0.1',
                          'SIL_icpr_location_n12000_simul_ow0.5_sw2.5_ft0.1',
                          'SIL_n12000_simul_ow0.5_sw2.5_ft0.1']

    x_values = []
    y_values = []
    outfile = open('plot_data.txt','w')
    for i in range(len(approaches_results_pathname)):
        path = approaches_results_pathname[i]
        x_values.append(range(1,11))
        performances = compute_rank_performance(root_path+'/'+path, script_path)
        print approaches[i],performances
        outfile.write(approaches[i])
        for j in range(len(performances)):
            outfile.write(','+str(performances[j]))
        outfile.write('\n')
        y_values.append(performances)
    outfile.close()

    plot_save_graphs(approaches, x_values, y_values)

if __name__ == '__main__':
    main()

