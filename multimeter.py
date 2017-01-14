""" generic definitions and base class for all multimeter types """
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
	VOLTAGE_DC:'Voltage DC', VOLTAGE_AC:'Voltage AC',
	CURRENT_DC:'Current DC', CURRENT_AC:'Current AC',
	RESISTANCE:'Resistance', VOLT_DIODE:'diode Voltage', 
	TEMP_INTERN:'internal temperature', TEMP_PT100:'temperature Pt100'}

def mmFunction(mmFunctionName):
	fnc=[key for key,value in mmFunctions.items() if value==mmFunctionName]
	return fnc[0]
	#mmFunctions.values().index(mmFunctionName)
	return mmFunctions.keys()[idx]
		
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
		
if __name__ == "__main__":
	print(mmFunction('Current DC'))
