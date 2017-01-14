""" top level multimeter abstraction to mooshimeter """
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
	mm.VOLTAGE_DC:('CH1:MAPPING 2|SHARED 0|CH1:ANALYSIS 0',(0.1,0.3,1.2)), 
	mm.VOLTAGE_AC:('CH1:MAPPING 2|SHARED 0|CH1:ANALYSIS 1',(0.1,0.3,1.2)), 
	mm.CURRENT_DC:('CH1:MAPPING 0|CH1:ANALYSIS 0',         (10)),
	mm.CURRENT_AC:('CH1:MAPPING 0|CH1:ANALYSIS 1',         (10)),
	mm.RESISTANCE:('CH1:MAPPING 2|SHARED 1|CH1:ANALYSIS 0',(1e3,1e4,1e5,1e6,1e7)),
	mm.VOLT_DIODE:('CH1:MAPPING 2|SHARED 2|CH1:ANALYSIS 0',(1.2)),
	mm.TEMP_INTERN:('CH1:MAPPING 1|CH1:ANALYSIS 0',        (350)),
	mm.TEMP_PT100:('CH1:MAPPING 2|SHARED 1|CH1:ANALYSIS 0',())
	}
	
mooshiFunc2 ={
	mm.VOLTAGE_DC:('CH2:MAPPING 0|CH2:ANALYSIS 0',(60,600)),
	mm.VOLTAGE_AC:('CH2:MAPPING 0|CH2:ANALYSIS 1',(60,600)),
	mm.RESISTANCE:('CH2:MAPPING 2|SHARED 1|CH2:ANALYSIS 0',(1e3,1e4,1e5,1e6,1e7)),
	mm.VOLT_DIODE:('CH2:MAPPING 2|SHARED 2|CH2:ANALYSIS 0',(1.2)),
	mm.TEMP_INTERN:('CH2:MAPPING 1|CH2:ANALYSIS 0',(350)),
	mm.TEMP_PT100:('CH2:MAPPING 2|SHARED 1|CH2:ANALYSIS 0',())
	}


class Mooshimeter (mm.Multimeter):
	""" interface to the mooshimeter multimeter using bluetooth on pythonista
	"""
		
	def __init__(self, periph_uid=None):
		""" search for mooshimeter devices with periph_uid in their peripheral UUID code
			gets command tree from the instrument 
		"""
		self._ch1ch2_callback=None
		self.ch_targets=[1.0,1.0]
		self.meter = MooshimeterDevice.MooshimeterDevice(periph_uid)
		self.kalive = self.keep_alive()
		
	def _results_callback(self, sval, scode):
		results = self.meter.get_values()
		if self._ch1ch2_callback is not None:
			self._ch1ch2_callback(results)	
		
	def set_results_callback(self, cb):
		self.meter.set_results_callback(self.meter.ch1Val_scode, self._results_callback)
		self.meter.set_results_callback(self.meter.ch2Val_scode, self._results_callback)
		self._ch1ch2_callback = cb
				
	def set_function(self, chan=1, mmFunction=None, target=float('nan')):
		if chan==2:
			fnc = mooshiFunc2
		else:
			fnc = mooshiFunc1
		if mmFunction is not None:
			cmds = fnc[mmFunction][0].split('|')
			for cmd in cmds:
				self.meter.send_cmd_string(cmd)
				time.sleep(0.2)
			if target==target: # not isnan
				rng=-1
				for trg in fnc[mmFunction][1]:
					rng+=1
					if float(target)<trg: # find closest range for target
						self.ch_targets[chan-1] = float(target)
						self.meter.send_cmd('CH%d:RANGE_I' % chan, rng)
						break
						
	def get_mmFunction(self,chan=1):
		isDC = self.meter.get_node_value('CH%d:ANALYSIS' % chan) == 0
		fnc = self.meter.get_node_value('CH%d:MAPPING' % chan)
		if fnc==2:
			shared = self.meter.get_node_value('SHARED')
			if shared==0:
				if isDC:
					return mm.VOLTAGE_DC
				else:
					return mm.VOLTAGE_AC
			elif shared==1:
				return mm.RESISTANCE
			elif shared==2:
				return mm.VOLT_DIODE
			else:
				logging.error('unknown shared:%d' % shared)
		elif fnc==1:
			return mm.TEMP_INTERN
		elif fnc==0:
			if chan==1:
				if isDC:
					return mm.CURRENT_DC
				else:
					return mm.CURRENT_AC
			elif chan==2:
				if isDC:
					return mm.VOLTAGE_DC
				else:
					return mm.VOLTAGE_AC
		else:
			logging.error('unknown mmFunc;%d for chan:%d DC:%d' % (fnc,chan,isDC))
			
	
	def trigger(self, trMode=1):
		self.meter.send_cmd('SAMPLING:TRIGGER', trMode)
	
	def get_value(self, chan=1):
		return self.meter.get_values()[chan-1]
		
	def keep_alive(self, t_interval=8.0):
		return tls.RepeatedTimer(t_interval, self.meter.send_cmd, 'TIME_UTC')
		
	def close(self):
		self.kalive.stop()
		self.meter.close()
			
		
if __name__ == "__main__":
	tls.set_logger()
	meter = Mooshimeter('FB55')       # ('FB55') is my meter (can be omitted for yours)
	time.sleep(2)
	meter.set_function(1, mm.RESISTANCE, 100)
	meter.set_function(2, mm.TEMP_INTERN)
	print('fnc: %s,%s' % (mm.mmFunctions[meter.get_mmFunction(1)],mm.mmFunctions[meter.get_mmFunction(2)]))
	meter.trigger(mm.trModes['continuous'])
	
	for i in range(40):
		print('v1:%f v2:%f' % (meter.get_value(1),meter.get_value(2)))
		time.sleep(1)
		
	meter.close()
	print('bye')
