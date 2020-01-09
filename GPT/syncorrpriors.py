
i1file = 'cmukitchen_act-obj.txt';
i2file = 'conceptnet_semantic_priors.txt';
o1file = open('x.txt','w');
o2file = open('y.txt','w');
with open(ifile,'r') as fp:
    for line in fp:
        lcontent = line.strip().split(',');
        data = lcontent[2:];
        ofile.write(lcontent[1].split(':')[1]);
        for col in data:
            ofile.write(','+col.split(':')[1]);
        ofile.write('\n');
