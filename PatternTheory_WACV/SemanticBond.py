import math as math

class SemanticBond:
	'Defines characteristics for bond type - Semantic - for a generator'
	#Constructor for initializing an instance of a Semantic bond
	def __init__(self, bondID, bondName, bondDir, currGenID):
		self.type = "Semantic" #Bond Type
		self.compatible = {} #Dictionary of compatible generators and compatability score
		self.name = bondName #Bond Name
		self.ID = bondID #Bond ID
		self.energy = 0  #Energy of bond. 0 if not active
		self.status = False #Status of bond. False if inactive, True if active
		self.currGen = currGenID #ID of the generator to which current bond belongs to
		# Bond Direction - IN(0) or OUT (1)
		if(bondDir == "IN"): 
			self.direction = 0
		elif(bondDir == "OUT"):
			self.direction = 1;
		else:
			raise ValueError('Bond Type must be either IN or OUT')
		self.compBondID = None #Complementary bond ID. i.e. ID of the bond on the other side of connection
		self.compGenID = None #Complementary generator ID. i.e. ID of the generator on the other side of connection

	# Function to get current Bond status. Returns the bond ID, Type and status as a tuple
	def getBondStatus(self):
		print "-------------------------Bond Status -------------------------------------------"
		print self.ID, self.type, self.status, self.compBondID, self.compGenID, self.currGen

	# Function to check bond compatability
	def checkCompatible(self, bond):
		return ((bond.type == self.type) and (bool(bond.direction) ^ bool(self.direction)) and (bool(bond.name == self.name)) and not (bond.status or self.status)) 
		# return true only if bonds are complementary (IN vs OUT)  -- got using XOR 
		# and compatible based on type -- if candidate bond type is same as self bond type

	# Bond Acceptor Function. Return energy:
	def calcEnergy(self, candidate, k=2.):
		# print "calcEnergy"
		score = self.compatible.get(candidate, None)
		energy = None
		if score is not None:
			energy = math.tanh(-k * score)
		return energy

	#Function to reset Bond to default:
	def resetBond(self):
		self.energy = 0
		self.status = False
		t1 = self.compBondID 
		self.compBondID = None
		t2 = self.compGenID
		self.compGenID = None
		# print t1, t2
		return t1, t2

	# Function to set current Bond to be active
	def formBond(self, bond, candLabel, candGenID): 
		# print "formBond"
		isCompatabile = self.checkCompatible(bond)
		if isCompatabile:
			t = self.calcEnergy(candLabel)
			if t == None:
				isCompatabile = False
				return (isCompatabile, bond)
			self.energy = t
			self.compBondID = bond.ID
			self.status = True
			self.compGenID = candGenID
			bond.status = True
			bond.energy = self.energy
			bond.compBondID = self.ID
			bond.compGenID = self.currGen
		return (isCompatabile, bond)