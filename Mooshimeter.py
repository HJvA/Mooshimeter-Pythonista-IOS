import MooshimeterDevice
import multimeter as mm
import logging
import time
import tls

logSTATE = {
	0:"OK",
	1:"No SD card detected",
	2:"SD card failed to mount - check filesystem",
	3:"SD card is full",
	4:"SD card write error",
	5:"END OF FILE" }

mooshiFunc1 ={ 
	mm.VOLTAGE_DC:'CH1:MAPPING 2|SHARED 0|ANALYSIS 0', # max 1.2V
	mm.VOLTAGE_AC:'CH1:MAPPING 2|SHARED 0|ANALYSIS 1', # max 1.2V
	mm.CURRENT_DC:'CH1:MAPPING 0|CH1:ANALYSIS 0',
	mm.CURRENT_AC:'CH1:MAPPING 0|CH1:ANALYSIS 1',
	mm.RESISTANCE:'CH1:MAPPING 2|SHARED 1|CH1:ANALYSIS 0',
	mm.VOLT_DIODE:'CH1:MAPPING 2|SHARED 2|CH1:ANALYSIS 0',
	mm.TEMP_INTERN  :'CH1:MAPPING 1|CH1:ANALYSIS 0',
	mm.TEMP_PT100:'CH1:MAPPING 2|SHARED 1|CH1:ANALYSIS 0'
	}
	
mooshiFunc2 ={
	mm.VOLTAGE_DC:'CH2:MAPPING 0|CH2:ANALYSIS 0',
	mm.VOLTAGE_AC:'CH2:MAPPING 0|CH2:ANALYSIS 1',
	mm.RESISTANCE:'CH2:MAPPING 2|SHARED 1|CH2:ANALYSIS 0',
	mm.VOLT_DIODE:'CH2:MAPPING 2|SHARED 2|CH2:ANALYSIS 0',
	mm.TEMP_INTERN  :'CH2:MAPPING 1|CH2:ANALYSIS 0',
	mm.TEMP_PT100:'CH2:MAPPING 2|SHARED 1|CH2:ANALYSIS 0'
	}
	



class Mooshimeter (mm.Multimeter):
	""" interface to the mooshimeter multimeter using bluetooth on pythonista
	having 
	"""
		
	def __init__(self, periph_uid=None):
		""" search for mooshimeter devices with periph_uid in their peripheral UUID code
			gets command tree from the instrument 
		"""
		self.ch1ch2_callback=None
		self.meter = MooshimeterDevice.MooshimeterDevice(periph_uid)
		
	def _results_callback(self, sval, scode):
		results = self.meter.get_values()
		if self.ch1ch2_callback is not None:
			self.ch1ch2_callback(results)	
		
	def set_results_callback(self, cb):
		self.meter.set_results_callback(self.meter.ch1Val_scode, self._results_callback)
		self.meter.set_results_callback(self.meter.ch2Val_scode, self._results_callback)
		self.ch1ch2_callback = cb
				
	def set_function(self, chan=1, mmFunction=None, target=float('nan')):
		if chan==2:
			fnc = mooshiFunc2
		else:
			fnc = mooshiFunc1
		if mmFunction is not None:
			cmd = fnc[mmFunction].split('|')
			for c in cmd:
				self.meter.send_cmd_string(c)
		
	
	def trigger(self, trMode=1):
		self.meter.send_cmd('SAMPLING:TRIGGER', trMode)
	
	def get_value(self, chan=1):
		return self.meter.get_values()[chan-1]
		
	def close(self):
		self.meter.close()
			
		
if __name__ == "__main__":
	tls.set_logger()
	meter = Mooshimeter('FB55')       # ('FB55') is my meter (can be omitted for yours)
	time.sleep(2)
	meter.set_function(1, mm.RESISTANCE, 100)
	meter.set_function(2, mm.TEMP_INTERN)
	meter.trigger(mm.trModes['continuous'])
	
	for i in range(10):
		print('v1:%f v2:%f' % (meter.get_value(1),meter.get_value(2)))
		time.sleep(1)
		
	meter.close()
	print('bye')
