import copy

class Generator:
	'Defines a new generator'
	# Constructor for initializing an instance of a generator

	def __init__(self, generatorID, generatorName, label, generatorType, feature):
		self.generatorID = generatorID #Defines the generator ID
		self.generatorName = generatorName # Defines the generator Name
		self.generatorType = generatorType # Defines the generator Type for hierarchy
		self.arity = 0 # Defines the arity (Number of active bonds) of the generator.
		self.inBonds = {} # Collection of the in bonds for the generator. Stored as a list.
		self.outBonds = {} # Collection of the in bonds for the generator. Stored as a list.
		self.label = label # Label candidate for the generator.
		self.openInBonds = 0 # Number of open in bonds
		self.openOutBonds = 0 # Number of open in bonds
		self.Active = False # Status flag for each generator. True if actively used in current configuration.
		self.coordinates = [] # List containing the spatial coordinate for the generator
		self.energy = 0 # Energy of the generator (sum of all its bond energies)
		self.feature = feature #Support feature
	
	# Function for adding a new in bond possibility to the generator
	def addInBond(self, bond):
		self.inBonds[bond.ID] = bond
		self.openInBonds += 1
		self.updateStatus()

	def removeInBond(self,bond):
		self.inBonds[bond.ID].resetBond()
		self.openInBonds += 1
		self.updateStatus()

	# Function for adding a new out bond possibility to the generator
	def addOutBond(self, bond):
		self.outBonds[bond.ID] = bond
		self.openOutBonds += 1
		self.updateStatus()

	def removeOutBond(self,bond):
		self.outBonds[bond.ID].resetBond()
		self.openOutBonds += 1
		self.updateStatus()

	def updateStatus(self):
		self.updateEnergy()
		self.arity = 0
		for b in self.inBonds.values():
			if b.status:
				self.arity += 1
		for b in self.outBonds.values():
			if b.status:
				self.arity += 1
		if self.arity < 1:
			self.Active = False
		else:
			self.Active = True

	# Function for adding a new bond connection to the generator
	def addBondConnection(self, bondID, candidateBond, label, candGenID):
		isValid, bond, direction = self.getBond(bondID)
		isCompatible = False
		b = None
		if(isValid):
			isCompatible, b = bond.formBond(candidateBond, label, candGenID)
			if isCompatible:
				if direction:
					self.openOutBonds -= 1
				else:
					self.openInBonds -= 1
				self.active = True
				self.arity += 1
		self.updateStatus()
		return (isCompatible, b)

	#Function to update the total energy of the generator
	def updateEnergy(self):
		bonds = self.inBonds.values() + self.outBonds.values()
		self.energy = 0
		for b in bonds:
			self.energy += b.energy
		# print self.energy

	# Function to get the current arity of the generator
	def getArity(self):
		return self.arity

	# Function to update bond status:
	def updateBond(self, bond):
		isValid, b, direction = self.getBond(bond.ID)
		# print isValid, b.ID, direction
		if isValid:
			if direction:
				del self.outBonds[b.ID]
				self.outBonds[b.ID] = bond
				
			else:
				del self.inBonds[b.ID]
				self.inBonds[b.ID] = bond
			self.active = True
			self.arity += 1
			self.updateStatus()
		return isValid

	#ID based bond lookup:
	def getBond(self, bondID):
		direction = None
		exists = False
		b = self.inBonds.get(bondID, None)
		if b is not None:
			direction = 0
			exists = True
		else:
			b = self.outBonds.get(bondID, None)
			if b is not None:
				direction = 1
				exists = True
		
		return (exists, b, direction)

	# Function for setting spatial coordinates to the generator
	def setCoords(self, coord):
		self.coordinates = coord

	# Function to get the generator details. Return ID, Name, Type, Arity and list of Bonds in a tuple.
	def getGeneratorDetails(self):
		print self.generatorID, self.generatorName, self.generatorType, self.arity
		for b in self.inBonds.values() + self.outBonds.values():
			b.getBondStatus()
		return (self.generatorID, self.generatorName, self.generatorType, self.arity, self.inBonds.values() + self.outBonds.values())

	#Function to reset generator to default state
	def resetGenerator(self):
		self.arity = 0 # Defines the arity (Number of active bonds) of the generator.
		self.Active = False # Status flag for each generator. True if actively used in current configuration.
		bonds = self.inBonds.values() + self.outBonds.values()
		strayBonds = []
		for b in bonds:
			strayBonds.append(b.resetBond())
		self.updateStatus()
		return strayBonds

	#Function to get energy without support bond:
	def swapEnergy(self):
		returnEnergy = self.energy
		for b in self.inBonds.values() + self.outBonds.values():
			if b.type == "Support":
				returnEnergy = returnEnergy - b.energy
				break
			else:
				continue
		return returnEnergy

	#Check spatial coherence -- to implement -- Fillipe IJCV
	def checkSpatialCoherence(self, candidateGenerator):
		# x_length = 0.0;
		# y_length = 0.0;

		# x_range = location.get_x_range();
		# y_range = location.get_y_range();

		# if self.__x_min <= x_range[0] and x_range[0] < self.__x_max:
		# 	x_length = min([self.__x_max - x_range[0], x_range[1] - x_range[0]]);
		# 	if self.__y_min <= y_range[0] and y_range[0] <= self.__y_max:
		# 		y_length = min([self.__y_max - y_range[0], y_range[1] - y_range[0]]);
		# 	elif y_range[0] <= self.__y_min and self.__y_min <= y_range[1]:
		# 		y_length = min([y_range[1] - self.__y_min, self.__y_max - self.__y_min]);
		# elif x_range[0] <= self.__x_min and self.__x_min < x_range[1]:
		# 	x_length = min([x_range[1] - self.__x_min,  self.__x_max - self.__x_min]);
		# 	if self.__y_min <= y_range[0] and y_range[0] <= self.__y_max:
		# 		y_length = min([self.__y_max - y_range[0], y_range[1] - y_range[0]]);
		# 	elif y_range[0] <= self.__y_min and self.__y_min <= y_range[1]:
		# 		y_length = min([y_range[1] - self.__y_min, self.__y_max - self.__y_min]);

		# intersect_area = x_length * y_length;
		# overlap_ratio = 0.0;
		# if intersect_area > 0.0:
		# 	overlap_ratio = intersect_area / float(max([(self.__x_max-self.__x_min)*(self.__y_max-self.__y_min),
		# 	(x_range[1]-x_range[0])*(y_range[1]-y_range[0])]));
		
		# return overlap_ratio;
		return 0;