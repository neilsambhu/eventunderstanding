#!/usr/bin/python

import math

class Bond:
    def __init__(self, type, value, coordinate=None, connector=None, energy=[0.0]):
        self.__marker = 'marker'                   # 'in' for in-bond or 'out' for out-bond
        self.__type = type                       # temporal, semantic, support
        self.__value = value                     # modality type or generator name
        self.__connector_coordinate = coordinate # connector's coordinate
        #self.__spatial_overlap_energy =
        self.__energy = energy					 #
        self.__connector = connector             # generator id
        self.__is_match = False
        self.__open_status = True
    #   self.__connector_pointer = connector_pointer

    #	def set_connector_pointer(self,connector_pointer):
    #		self.__connector_pointer = connector_pointer

    def is_open(self):
        return self.__open_status

    def set_marker(self,marker):
        self.__marker = marker if marker in ['in','out'] else None

    def set_value(self,value):
        self.__value = value

    def set_is_match(self,state):
        self.__is_match = state

    def get_match_state(self):
        return self.__is_match

    def set_energy(self,energy):
        self.__energy = energy

    def set_connector_coordinate(self,coordinate):
        self.__connector_coordinate = coordinate

    def set_connector(self,connector):
        self.__connector = connector

    def get_type(self):
        return self.__type

    def get_value(self):
        return self.__value

    def get_marker(self):
        return self.__marker

    def compute_energy(self,weight=1.):
        pass

    def get_energy(self,weight=1.):
        sum = 0.0
        for i in range(len(self.__energy)):
            sum += self.__energy[i]
        return sum * weight

    def get_connector(self):
        return self.__connector

    def get_connector_coordinate(self):
        return self.__connector_coordinate

    #	def get_connector_pointer(self):
    # 		return self.__connector_pointer

    def get_copy(self):
        bond = Bond(self.__type,self.__value,self.__connector_coordinate,
                    self.__connector,self.__energy)
        bond.set_marker(self.__marker)
        return bond

    def remove_connector(self):
        energy = self.__energy
        connector = self.__connector
        self.__connector_coordinate = None
        self.__energy = [ 0.0 ]
        self.__connector = None
        self.__is_match = False # for performance rate measurement
        # in case the values of the connection are useful for post removal
        return ( connector, energy )

    def print_info(self):
        info_string = '    ' + self.__marker + '-Bond = value:'+repr(self.__value)+', energy:'+repr(self.__energy) + ' type: ' + self.__type
        info_string += ', connector:'+repr(self.__connector)
        info_string += ', connector coordinate:'+repr(self.__connector_coordinate)
        print info_string
