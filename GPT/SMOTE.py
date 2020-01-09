#!/home/students/fillipe/anaconda/bin/python

import sys
import scipy
import numpy as np
import random as rd

class SMOTE:
    def k_nearest_neighbors(self,data,nsamples,k=1):
        kneighbors = []
        dtype = [('index', int), ('distance', float)]
        #k = k if k < nsamples else int(nsamples/2)+1
        for j in range(nsamples):
            sample = data[j]
            distances = np.array([(i, scipy.inner(sample-data[i],sample-data[i])) for i in range(len(data))],dtype=dtype)
            distances.sort(order='distance')
            kneighbors.append(distances[1:k+1])
            #print repr(kneighbors)

        return kneighbors

    def smote(self,filename,smoteamount=1.0,k=1):
        # amount of smote (a fraction or multiple of the original number of samples)
        #smoteamount = 3 # .75 means 75% and 2 means 200%
        if smoteamount <= 0.0:
            return filename

        # load data from file into narray data structure
        filedata = np.loadtxt(filename)
        #print 'Loading ',filename,'into memory...'
        #print repr(filedata)

        # get number of samples (feature points) in the file
        ninstances = len(filedata)
        k = k if k < ninstances else int(ninstances/2)+1

        # get number of dimensions of each sample (or feature point)
        #nattributes = 0 if len(filedata) < 1 else len(filedata[0])

        #print 'Update SMOTE amount and number '
        # shuffle the instances in place if the amount of smote is less than 100%
        if smoteamount < 1.0:
            np.random.shuffle(filedata)
            ninstances = int(smoteamount * ninstances)
            smoteamount = 1

        smoteamount = int(smoteamount)
        print 'Amount of SMOTE:',smoteamount,'# Instances:',ninstances

        # find the k nearest neighbors for each minority class sample
        #data = filedata[0:ninstances,:]
        #print 'data length:',len(data),'nsamples',ninstances

        # only use the
        print "Find k nearest neighbors of original samples..."
        kneighbors = self.k_nearest_neighbors(filedata,ninstances,k)

        #print 'Generate synthetic samples...'   
        synthetic_samples = []
        while smoteamount > 0:
            print 'sample',smoteamount
            #print 'data len',len(filedata),'kneighbors len:',len(kneighbors)
            for i in range(ninstances):
                # select one of the neighbor of sample i
                neighbor_index = rd.randrange(k)
                # number between 0.0 and 1.0
                gap = rd.random()
                #print 'neighbor_index',neighbor_index,'i',i,'len(kneighbors[i])',len(kneighbors[i]),'len(kneighbors[i][neighbor_index])',len(kneighbors[i][neighbor_index]),'kneighbors[i][neighbor_index]',kneighbors[i][neighbor_index]
                # create and save new synthetic sample
                diff = filedata[kneighbors[i][neighbor_index]['index']] - filedata[i]
                synthetic_samples.append(filedata[i] - gap * diff)
                # print 'original sample:',repr(filedata[i])
                # print 'closest k sample:',repr(filedata[kneighbors[i][neighbor_index]['index']])
                # print 'diff',repr(diff),'gap',gap
                # print 'new synthetic sample:',repr(synthetic_samples[-1])
            smoteamount -= 1

        # save new synthetic samples on disk

        np.savetxt(filename+'.smote',np.concatenate((filedata,synthetic_samples), axis=0),"%g")

        return filename+'.smote'

def test_cases():
    smote = SMOTE()

    k = 3
    smote_amount = .5
    filename = 'test_file1.txt'
    smote.smote(filename, smote_amount, k)

    k = 6
    smote_amount = 2.5
    filename = 'test_file2.txt'
    smote.smote(filename, smote_amount, k)

def main():

    if len(sys.argv) < 2:
        print './smote filename.txt smote_amount k'
        print '\nNotes:\n-- smote_amount : float value > 0 (default: 1), where 1 means 100%'
        print '-- k : number of nearest neighbors (default: 1)\n-- the output file is named filename.txt.smote'
        exit(1)

    filename = sys.argv[1]
    smote_amount = .5 if len(sys.argv) < 3 else float(sys.argv[2])
    k = 1 if len(sys.argv) < 4 else int(sys.argv[3])

    smote = SMOTE()
    smote.smote(filename, smote_amount, k)

if __name__ == '__main__':
    main()
