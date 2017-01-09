import MooshimeterDevice
import multimeter
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
	
chVOLTDC=0
mooshi_chan_lod = [
	{}
	]	
	


class Mooshimeter (multimeter.Multimeter):
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
				
	def trigger(self, trMode=1):
		self.meter.send_cmd('SAMPLING:TRIGGER', trMode)
	
	def get_value(self, chNr=1):
		return self.meter.get_values()[chNr]
		
	def close(self):
		self.meter.close()
			
		
if __name__ == "__main__":
	tls.set_logger()
	meter = Mooshimeter('FB55')       # ('FB55') is my meter (can be omitted for yours)
	time.sleep(2)
	meter.trigger(trModes['continuous'])
	
	for i in range(10):
		print('v1:%f' % meter.get_value())
		time.sleep(1)
		
	meter.close()
	print('bye')
