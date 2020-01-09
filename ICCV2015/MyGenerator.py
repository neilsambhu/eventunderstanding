#!/usr/bin/python

from Generator import *

import os
import glob
import string

class MyGenerator(Generator):

    def read_result(self,filename):
        file = open(filename)
        line = file.readline()
        file.close()
        return float(line.replace('\n',''))

    def __get_xy_min_max(self,points):
        xymin = [points[0][0],points[0][1]]
        xymax = [points[0][0],points[0][1]]
        for p in points:
            if p[0] < xymin[0]:
                xymin[0] = p[0]
            elif p[0] > xymax[0]:
                xymax[0] = p[0]
            if p[1] < xymin[1]:
                xymin[1] = p[1]
            elif p[1] > xymax[1]:
                xymax[1] = p[1]

        return (xymin,xymax)

    def act_obj_local_weight(self,action_files_path,object_filename):
        data = string.split(action_files_path,'/')
        act_filename = data[len(data)-1]
        data = string.split(object_filename,'/')
        obj_filename = data[len(data)-1]

        result_filename = act_filename + '_' + obj_filename + '.sls'
        if os.path.isfile(result_filename) == True:
            return self.read_result(result_filename)

        result_file = open(result_filename,'w')

        object_bbox_file = open(object_filename)

        overlaps_per_frame = [0.0001]
        for line in object_bbox_file:
            data = string.split(line.replace('\n',''),',')
            frame_number = data[0]
            frame_flow_points_filename = action_files_path + '/frame_' + frame_number + '.txt'

            if os.path.isfile(frame_flow_points_filename) == True and os.path.getsize(frame_flow_points_filename) > 0:
                # motion vector data
                frame_flow_points_file = open(frame_flow_points_filename)

                iline = frame_flow_points_file.readline()
                data2 = string.split(iline.replace('\n',''),',')
                flow_frame_width = float(data2[0])
                flow_frame_height = float(data2[1])

                # object bounding box data
                frame_width = float(data[1])
                frame_height = float(data[2])
                top_left_x = (flow_frame_width/frame_width)*float(data[3])
                top_left_y = (flow_frame_height/frame_height)*float(data[4])
                bottom_right_x = (flow_frame_width/frame_width)*(float(data[3])+float(data[5]))
                bottom_right_y = (flow_frame_width/frame_width)*(float(data[4])+float(data[6]))

                total_area = (bottom_right_y-top_left_y)*(bottom_right_x-top_left_x)

                count = 0.0
                total = 0.0
                # MODIFY THIS:
                #    check the point inside the box, find minimum and maximum point,
                #    compute the percentage of the bounding boxes formed by min and max inside the object box

                inside_points = []
                for iline in frame_flow_points_file:
                    data2 = string.split(iline.replace('\n',''),',')
                    x = float(data2[0])
                    y = float(data2[1])

                    if x >= top_left_x and x <= bottom_right_x:
                        if y >= top_left_y and y <= bottom_right_y:
                            count += 1.0
                            inside_points.append([x,y])

                    total += 1.0
                frame_flow_points_file.close()

                # old count: overlap by number of points
                #				overlaps_per_frame.append(count/total)
                #				print 'overlap is ' + repr(count/total)

                # new count: overlap by accounted area
                overlap_area = 0
                if len(inside_points) > 0:
                    xymin,xymax = self.__get_xy_min_max(inside_points)
                    overlap_area = (xymax[0]-xymin[0])*(xymax[1]-xymin[1])

                overlaps_per_frame.append(overlap_area/total_area)

        object_bbox_file.close()
        overlaps_per_frame.sort(reverse=True)

        result_file.write(repr(overlaps_per_frame[0]))
        result_file.close()

        return overlaps_per_frame[0]

    def obj_obj_local_weight(self,g):

        obj1_filename = self.get_rlocation()
        obj2_filename = g.get_rlocation()

        data = string.split(obj1_filename,'/')
        ob1_filename = data[len(data)-1]
        data = string.split(obj2_filename,'/')
        ob2_filename = data[len(data)-1]

        result_filename = ob1_filename + '_' + ob2_filename + '.sls'
        #		print result_filename
        if os.path.isfile(result_filename) == True:
            return self.read_result(result_filename)

        result_file = open(result_filename,'w')

        obj1_file_content = {}
        object_bbox_file = open(self.get_rlocation())
        for line in object_bbox_file:
            data = string.split(line.replace('\n',''),',')
            frame_number = data[0]
            obj1_file_content[frame_number] = line
        object_bbox_file.close()

        obj2_file_content = {}
        object_bbox_file = open(g.get_rlocation())
        for line in object_bbox_file:
            data = string.split(line.replace('\n',''),',')
            frame_number = data[0]
            obj2_file_content[frame_number] = line
        object_bbox_file.close()

        overlaps_per_frame = [0.0001]
        for key1 in obj1_file_content:
            data = string.split(obj1_file_content[key1].replace('\n',''),',')
            frame_number = data[0]

            if frame_number in obj2_file_content:
                data2 = string.split(obj2_file_content[frame_number].replace('\n',''),',')
                obj2_frame_number = data2[0]

                changed = False
                x_length = 0.0
                y_length = 0.0

                p1_x = float(data[3])
                p1_y = float(data[4])
                p1_w = float(data[5])
                p1_h = float(data[6])

                p2_x = float(data2[3])
                p2_y = float(data2[4])
                p2_w = float(data2[5])
                p2_h = float(data2[6])

                if p2_x < p1_x:
                    changed = True
                    p2_x = float(data[3])
                    p2_y = float(data[4])
                    p2_w = float(data[5])
                    p2_h = float(data[6])
                    p1_x = float(data2[3])
                    p1_y = float(data2[4])
                    p1_w = float(data2[5])
                    p1_h = float(data2[6])

                #				print 'p1x,p1y = ' + repr(p1_x) + ',' + repr(p1_y) + ' p1w,p1h = ' + repr(p1_x+p1_w) + ',' + repr(p1_y+p1_h)
                #				print 'p2x,p2y = ' + repr(p2_x) + ',' + repr(p2_y) + ' p2w,p2h = ' + repr(p2_x+p2_w) + ',' + repr(p2_y+p2_h)

                # if overlap along the x axis
                if p1_x <= p2_x and p2_x <= (p1_x + p1_w):
                    x_length = min([p1_x + p1_w - p2_x,p2_w])
                    # check for overlap along y axis
                    if p1_y <= p2_y and p2_y <= (p1_y + p1_h):
                        y_length = min( [ p1_y + p1_h - p2_y, p2_h ] )
                    elif p2_y <= p1_y and p1_y <= (p2_y + p2_h):
                        y_length = min( [ p2_y + p2_h - p1_y, p1_h ] )

                intersect_area = x_length * y_length
                intersect_area_ratio = intersect_area / (p1_w * p1_h)
                if changed == True:
                    intersect_area_ratio = intersect_area / (p2_w * p2_h)

                overlaps_per_frame.append(intersect_area_ratio)

            #				print 'xlength:'+repr(x_length) + ' ylength:' + repr(y_length)
            #				if intersect_area > 0.0:
            #					print frame_number + ' intersect area: ' + repr(intersect_area) + ' obj1_ratio: ' + repr(intersect_area_ratio)

            overlaps_per_frame.sort(reverse=True)

        result_file.write(repr(overlaps_per_frame[0]))
        result_file.close()

        return overlaps_per_frame[0]

    # def get_overlap_energy(self,g):
    def get_spatial_overlap_ratio(self,g):
        #	    print self.get_name() + ' <-> ' + g.get_name()
        if 'hog' in g.get_modality() + self.get_modality() or 'hof' in g.get_modality() + self.get_modality() :
            return 0.0001
        elif 'action' in self.get_modality() and 'action' not in g.get_modality():
            return self.act_obj_local_weight(self.get_rlocation(),g.get_rlocation())
        elif 'action' not in self.get_modality() and 'action' in g.get_modality():
            return self.act_obj_local_weight(g.get_rlocation(),self.get_rlocation())
        elif 'action' in self.get_modality() and 'action' in g.get_modality():
            return 1.0
        else:
            return self.obj_obj_local_weight(g)
			