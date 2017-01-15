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
	VOLTAGE_DC:('Voltage DC','V'), VOLTAGE_AC:('Voltage AC','V'),
	CURRENT_DC:('Current DC','A'), CURRENT_AC:('Current AC','A'),
	RESISTANCE:('Resistance','Ω'), VOLT_DIODE:('diode Voltage','V'), 
	TEMP_INTERN:('internal temperature','K'), TEMP_PT100:('temperature Pt100','°C')}

def mmFunction(mmFunctionName):
	fnc=[key for key,value in mmFunctions.items() if value[0]==mmFunctionName]
	return fnc[0]
		
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
	fnc=CURRENT_AC
	fncnm=mmFunctions[fnc][0]
	fncun=mmFunctions[fnc][1]
	print('%s (=%d) %s [%s]' % (mmFunction(fncnm),fnc,fncnm,fncun))
