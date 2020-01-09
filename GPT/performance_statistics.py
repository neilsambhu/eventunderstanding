#!/usr/bin/python

import string

def main():
    total_videos = 0.0
    low_clutter = 0
    high_clutter = 1
    good_recall = [[],[]]
    bad_recall = [[],[]]
    good_precision = [[],[]]
    bad_precision = [[],[]]
    good_precision_feat = [[],[]]
    bad_precision_feat = [[],[]]
    baseline_feature_precision = [[],[]]
    filename = 'clutter_of_objects_performance_exp3400.csv'
    file = open(filename,'r')
    for line in file:
        line = line.replace('\n','')
        data = string.split(line,',')
        videoname = data[0]
        clutter = float(data[1])
        recall = float(data[2])
        precision = float(data[3])
        precision_feat = float(data[7])
        
        if recall > 0.5:
            if clutter > 0.4:
                good_recall[high_clutter].append(videoname)
            else:
                good_recall[low_clutter].append(videoname)
        else:
            if clutter > 0.4: 
                bad_recall[high_clutter].append(videoname)
            else:
                bad_recall[low_clutter].append(videoname)
        
        if precision > 0.05:
            if clutter > 0.4:
                good_precision[high_clutter].append(videoname)
            else:
                good_precision[low_clutter].append(videoname)
        else:
            if clutter > 0.3: 
                bad_precision[high_clutter].append(videoname)
            else:
                bad_precision[low_clutter].append(videoname)
                
        if precision_feat > 0.5:
            if clutter > 0.4:
                good_precision_feat[high_clutter].append(videoname)
            else:
                good_precision_feat[low_clutter].append(videoname)
        else:
            if clutter > 0.4: 
                bad_precision_feat[high_clutter].append(videoname)
            else:
                bad_precision_feat[low_clutter].append(videoname)
        
        if clutter > 0.4:
            if 1. - clutter > 0.5: 
                baseline_feature_precision[0].append(videoname)    
            else:
                baseline_feature_precision[1].append(videoname)
        total_videos += 1.0
             
    file.close()
    
    for clutter in [low_clutter, high_clutter]:
        if clutter == low_clutter:
            print 'low clutter - high recall ' + repr(len(good_recall[low_clutter])/total_videos) + ': ' + repr(good_recall[low_clutter])
            print 'low clutter - low recall ' + repr(len(bad_recall[low_clutter])/total_videos) + ': ' + repr(bad_recall[low_clutter])
        else:
            print 'high clutter - high recall ' + repr(len(good_recall[high_clutter])/total_videos) + ': ' + repr(good_recall[high_clutter])
            print 'high clutter - low recall ' + repr(len(bad_recall[high_clutter])/total_videos) + ': ' + repr(bad_recall[high_clutter])
            
    for clutter in [low_clutter, high_clutter]:
        if clutter == low_clutter:
            print 'low clutter - high precision ' + repr(len(good_precision[low_clutter])/total_videos) + ': ' + repr(good_precision[low_clutter])
            print 'low clutter - low precision ' + repr(len(bad_precision[low_clutter])/total_videos) + ': ' + repr(bad_precision[low_clutter])
        else:
            print 'high clutter - high precision ' + repr(len(good_precision[high_clutter])/total_videos) + ': ' + repr(good_precision[high_clutter])
            print 'high clutter - low precision ' + repr(len(bad_precision[high_clutter])/total_videos) + ': ' + repr(bad_precision[high_clutter])
            
    intersection = list(set(good_precision_feat[high_clutter]) & set(bad_precision[high_clutter]))        
    print 'intersect ' + repr(len(intersection)) + ' ' + repr((1.0*len(intersection))/(len(good_precision[high_clutter])+len(bad_precision[high_clutter]))) + '  list: ' + repr(intersection)
     
    print 'high clutter - high feature precision ' + repr(len(good_precision_feat[high_clutter])/(1.0*(len(bad_precision_feat[high_clutter])+len(good_precision_feat[high_clutter])))) 
    print 'high clutter - high feature precision ' + repr((1.*len(baseline_feature_precision[0]))/(len(baseline_feature_precision[0])+len(baseline_feature_precision[1])))

if __name__ == '__main__':
    main()