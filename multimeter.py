trModes = {'stop':0, 'once':1, 'continuous':2}

VOLTAGE_DC=1
VOLTAGE_AC=2
CURRENT_DC=3
CURRENT_AC=4
RESISTANCE=5
VOLT_DIODE=6
TEMP_INTERN=7
TEMP_PT100=8

mmFunctions = {
	'Voltage DC':VOLTAGE_DC, 'Voltage AC':VOLTAGE_AC,
	'Current DC':CURRENT_DC, 'Current AC':CURRENT_AC,
	'Resistance':RESISTANCE, 'diode Voltage':VOLT_DIODE, 
	'internal temperature':TEMP_INTERN, 'temperature Pt100':TEMP_PT100}

class Multimeter (object):
	"""
	"""
	def __init__(self, identifyer=None):
		pass
	
	def channel_choices(self, chan):
		pass
		
	def set_function(self,chan=1, mmFunction=None, target=float('nan')):
		pass
		
	def trigger(self, trMode):
		pass
		
	def get_value(self, chan):
		pass
		
