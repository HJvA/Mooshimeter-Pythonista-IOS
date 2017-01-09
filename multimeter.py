trModes = {'stop':0, 'once':1, 'continuous':2}

mmFunctions = {'Voltage DC':0, 'Voltage AC':2,'Current DC':3,'Current AC':4,'Resistance':5}

class Multimeter (object):
	"""
	"""
	def __init__(self, identifyer=None):
		pass
	
	def channel_choices(self, chNr):
		pass
		
	def trigger(self, trMode):
		pass
		
	def get_value(self, chNr):
		pass
		
