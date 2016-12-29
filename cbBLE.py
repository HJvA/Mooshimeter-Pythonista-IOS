import cb
import tls
import time
from collections import deque

cbPropMsg = [
	(cb.CH_PROP_AUTHENTICATED_SIGNED_WRITES,'Authenticated'),
	(cb.CH_PROP_BROADCAST,'Broadcast'),
	(cb.CH_PROP_EXTENDED_PROPERTIES,'Extended'),
	(cb.CH_PROP_INDICATE,'Indicate'),
	(cb.CH_PROP_INDICATE_ENCRYPTION_REQUIRED,'Encryption Required'),
	(cb.CH_PROP_NOTIFY,'Notify'),
	(cb.CH_PROP_NOTIFY_ENCRYPTION_REQUIRED,'Notif.Encr.Req'),
	(cb.CH_PROP_READ,'Read'),
	(cb.CH_PROP_WRITE,'Write'),
	(cb.CH_PROP_WRITE_WITHOUT_RESPONSE,'Write no response')
	]

chPERF =0
chID =1
chPUID =2
chCUID =3

def MaskedPropMsg(msgDict,bitmask):
	lst = (k[1] for k in msgDict if k[0] & bitmask)
	return ','.join(lst)

				
class bleDelegate (object):
	"""
	"""
	def __init__(self,lodBLE):
		"""
		"""
		#self.perfName = peripheralName
		self.peripherals = []
		self.lodCharist=lodBLE
		ar = (r[chPERF] for r in self.lodCharist)
		print('### ble Scanning %d peripherals ###' % len(set(ar)))
		self.chQueue = deque()  #queue.Queue()
		self.charFound =[]
		self.respCallback=self._exampleRespCallback

	def close(self):
		"""
		"""
		cb.reset()
		
	def allFound(self):
		if len(self.chQueue)>0:
			return False
		if len(self.charFound)==0:
			return False
		return len(self.charFound)>=len(self.lodCharist)
		charCnt=0
		for chRec in self.charFound:
			perf=chRec['periph']
			isin = query_lod(self.lodCharist, lambda rw:rw[chPERF] in perf.name)	
			charCnt += len(isin)
		return len(self.charFound) >= charCnt

	def _inLod(self,perf):
		if not perf.name:
			return []
		isin = tls.query_lod(self.lodCharist, 
			lambda rw:rw[chPERF] in perf.name and (not rw[chPUID]) and rw[chCUID])
		if not isin:
			isin = tls.query_lod(self.lodCharist, 
				lambda rw: (rw[chPUID] and rw[chPUID] in perf.uuid))
		if not isin:
			isin = tls.query_lod(self.lodCharist, 
				lambda rw:rw[chPERF] in perf.name and (not rw[chPUID]) and (not rw[chCUID]))
		return isin

	def PerfQueueSyncer(self,perf):
		isin = self._inLod(perf) 
		if not isin:
			print('nothing assigned for perf:%s' % perf.name)
			return False
		else:
			tmo=5 # timeout
			while len(self.chQueue)>0:  
				print("still waiting for discovery n:%d state:%d" % (len(self.chQueue),cb.get_state()))
				time.sleep(1)
				if tmo<=0:
					p=self.chQueue.pop()
					print('timeout for peripheral %s' % p.name)
				tmo-=1
			#self.chQueue.join()  # wait for all characteristics found	
			for d in isin:
				self.chQueue.append(perf)
			return True		
									
	def did_discover_peripheral(self, p):
		if not p.name:
			return
		isin = self._inLod(p)			
		print('testing peripheral: %s state %d (%s) isin:%d' % (p.name,p.state, p.uuid, len(isin)))
		if p.state > 0: # allready connecting
			return
		if len(isin)>0:	# matching lod
			#self.charFound.append(dict(perf=p))
			self.peripherals.append(p) # keep reference!
			print('connecting %s' % p.name)
			cb.connect_peripheral(p)
			
	def did_connect_peripheral(self, p):
		print('*** Connected: %s (%s)' % (p.name,p.uuid))		
		p.discover_services()

	def did_fail_to_connect_peripheral(self, p, error):
		print('Failed to connect %s because %s' % (p.name,error))
		#self.peripherals.remove(p)

	def did_disconnect_peripheral(self, p, error):
		print('Disconnected %s, error: %s' % (p.name,error))
		self.peripherals.remove(p)

	def did_discover_services(self, p, error):
		print('found %d services for %s (%s) busy:%d' % (len(p.services),p.name,p.uuid,len(self.chQueue)))
		if self.PerfQueueSyncer(p):
			print('discovering characteristics n:%d for %s' % (len(self.chQueue),p.name))
			for s in p.services:
				p.discover_characteristics(s)
			
	def did_discover_characteristics(self, s, error):
		print('%d characteristics for serv:%s (prim:%s)' % (len(s.characteristics),s.uuid,s.primary))
		for c in s.characteristics:
			if len(self.chQueue)==0:   #.empty():
				print('nothing to discover anymore for act peripheral')
				break
			else:
				perf =self.chQueue[-1] # preview
				for lodr in self._inLod(perf): # perf matches crit
					isFnd,idx = tls.lookup_lod(self.charFound, chId=lodr[chID] )
					if isFnd is not None:
						print('id %d allready found with %s' % (lodr[chID],c.uuid)) # should not happen
					elif not lodr[chCUID] or lodr[chCUID] in c.uuid:
						perf = self.chQueue.pop()  #get(False)
						print("++ charist %d %s (notif:%d)-->%s" %
							(lodr[chID],c.uuid,c.notifying, MaskedPropMsg(cbPropMsg,c.properties)))
						self.charFound.append(dict(chId=lodr[chID], periph=perf, charis=c))
						break
						
						if c.properties & cb.CH_PROP_WRITE:
							perf.set_notify_value(c, True)
							perf.write_characteristic_value(c,bytes([0x00,0x01]))
						self.chCount += 1
						break
						#self.chQueue.task_done()

	def did_write_value(self, c, error):
		#print('Did write val to c:%s' % (c.uuid,))
		pass

	def did_update_value(self, c, error):
		if self.respCallback is None:
			sval = ''.join('{:02x}'.format(x) for x in c.value)
			print('Updated value: %s from %s' % (sval,c.uuid))
		else:
			self.respCallback(c.value)
		
	def did_update_state(self):
		print('update state:%s' % self.peripheral.state)	
									
	def write_characteristic(self,chId,chData):
		"""
		"""
		rec,idx = tls.lookup_lod(self.charFound, chId=chId)
		rec['periph'].write_characteristic_value(rec['charis'], chData)

	def read_characteristic(self,chId):
		"""
		"""
		rec,idx = tls.lookup_lod(self.charFound, chId=chId)
		rec['periph'].read_characteristic_value(rec['charis'])

	def setup_response(self,charId,respCallback=None):
		"""
		"""
		rec,idx = tls.lookup_lod(self.charFound, chId=charId)
		p=rec['periph']
		c=rec['charis']
		print('setup response for %s with prop:%s notif:%d' % (p.name,MaskedPropMsg(cbPropMsg,c.properties),c.notifying))
		#if respCallback is not None:
		self.respCallback = respCallback
		if c.notifying:
			return
			p.set_notify_value(c, True)
		elif c.properties & cb.CH_PROP_INDICATE:
			#self.peripheral.set_notify_value(c, True)
			p.read_characteristic_value(c)
		elif c.properties & cb.CH_PROP_NOTIFY:
			p.set_notify_value(c, True)
					
	def _exampleRespCallback(self,cValue):	
		sval = ''.join('{:02x}'.format(x) for x in cValue)
		print('Updated value: %s from %s' % (sval,'?!'))
		
			
def discover_BLE_characteristics(lodBLE):
	"""
	"""
	cb.set_verbose(True)
	cb.reset()
	Delg = bleDelegate(lodBLE)	
	cb.set_central_delegate(Delg)
	cb.scan_for_peripherals()
	print('Waiting for callbacks state=%s' % (cb.get_state()))
	while not Delg.allFound():
		time.sleep(1)
	print('found %d characteristics' % len(Delg.charFound))
	cb.stop_scan()
	#cb.reset()
	return Delg	
	
	
if __name__=="__main__":
	PerfName='Mooshi'
	SERIN = 0
	SEROUT = 1
	#lod = [dict(perf=PerfName, id=i, puid=None, cuid=None) for i in (SERIN,SEROUT)]	
	lod = [{chPERF:PerfName, chID:i, chPUID:None, chCUID:None} for i in (SERIN,SEROUT)]
	lod[SERIN][chCUID] = 'FFA1' 
	lod[SEROUT][chCUID] = 'FFA2'
	cbDelg = discover_BLE_characteristics(lod)
	cbDelg.write_characteristic(SERIN, bytes([0x00,0x01]))
	#print(tls.lookup_lod(cbDelg.charFound, chId=1))
	cbDelg.setup_response(SEROUT)
	time.sleep(10)
	cb.reset()
	print('bye')
