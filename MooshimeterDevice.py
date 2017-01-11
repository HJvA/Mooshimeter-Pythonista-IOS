import cbBLE
import tls
import time
import zlib
import binascii
import struct
import logging

SERIN  = 0
SEROUT = 1

dtPLAIN   =0
dtLINK    =1
dtCHOOSER =2
dtU8      =3
dtU16     =4
dtU32     =5
dtS8      =6
dtS16     =7
dtS32     =8
dtSTR     =9
dtBIN     =10
dtFLT     =11

dtTypes = {	# (nBytes, Signed, Name, struct.pack_code)
	dtPLAIN  :(0,False,'PLAIN'),
	dtLINK   :(0,False,'LINK'),
	dtCHOOSER:(1,False,'CHOOSER','B'),
	dtU8     :(1,False,'U8',     'B'),
	dtU16    :(2,False,'U16',    '<H'),
	dtU32    :(4,False,'U32',    '<I'), # lsb of time_utc at front
	dtS8     :(1,True,'S8',      'b'),
	dtS16    :(2,True,'S16',     '<h'),
	dtS32    :(4,True,'S32',     '<i'),
	dtSTR    :(0,False,'STR',    's'),
	dtBIN    :(0,False,'BIN'),
	dtFLT    :(4,True,'FLT',     'f')
	}

logSTATE = {
	0:"OK",
	1:"No SD card detected",
	2:"SD card failed to mount - check filesystem",
	3:"SD card is full",
	4:"SD card write error",
	5:"END OF FILE" }

class MooshimeterDevice (object):
	""" interface to the mooshimeter multimeter using bluetooth on pythonista
	"""
		
	def __init__(self, periph_uid=None):
		""" search for mooshimeter devices with periph_uid in their peripheral UUID code
			gets command tree from the instrument 
		"""
		lod = [
			{cbBLE.chPERF:'Mooshi', cbBLE.chID:SERIN,  cbBLE.chPUID:periph_uid, cbBLE.chCUID:'FFA1'},
			{cbBLE.chPERF:'Mooshi', cbBLE.chID:SEROUT, cbBLE.chPUID:periph_uid, cbBLE.chCUID:'FFA2'}
			]
		self.cbDelg = cbBLE.discover_BLE_characteristics(lod)
		self.cbDelg.setup_response(SEROUT,self._receive_node_callback)
		self.cbDelg.write_characteristic(SERIN, bytes([0x00,0x01])) # request command tree
		self.aggregate = bytearray()
		self.seq_n =None
		self.cmd_tree = []
		self.snode_vals ={}
		self.snode_callbacks={}
		self.ch1Val_scode = self.ch2Val_scode = None
		#self.newVal=False
		#self.newResultsCallback=self._new_results
		
	def close(self):
		""" diconnect BLE; release resources
		"""
		self.cbDelg.close()
		
	def _new_results(self,newResultsList):
		pass
		
	def _receive_node_callback(self,cValue):
		seq_n = cValue[0] & 0xFF
		if self.seq_n is not None and seq_n != (self.seq_n+1)%0x100:
			logging.error ('Received out of order packet! Expected:%d, got:%d' % (self.seq_n+1, seq_n))
		self.seq_n = seq_n
		self.aggregate += cValue[1:] # append block and strip sequence number
		shortcode=self.aggregate[0]
		if shortcode==1: # receiving tree, unknown lod yet
			if self._parse_cmd_tree():
				self.send_cmd('TIME_UTC', int(tls.seconds_since_epoch()))     # set correct time_utc
				self.ch1Val_scode = self._lookup_node('CH1:VALUE')['scode']
				self.ch2Val_scode = self._lookup_node('CH2:VALUE')['scode']
				self.snode_vals[self.ch1Val_scode]=float('nan')
				self.snode_vals[self.ch2Val_scode]=float('nan')
				logging.info('received tree items:%d ch1Val_scode:%d' % (len(self.cmd_tree),self.ch1Val_scode))
		elif shortcode==5:  # TIME_UTC but may have other results
			if 5<len(self.aggregate)<23:
				pass
			else:
				self.assign_sval(shortcode, self.bytes_to_var(self.aggregate[1:5], dtU32))
				logging.info('t utc %d len(%d)' % (self.snode_vals[shortcode],len(self.aggregate)))
				if len(self.aggregate) >= 23:
					#self.newVal=True
					val1 = self.bytes_to_var(self.aggregate[5:9], dtU32)
					self.assign_sval(self.ch1Val_scode, self.bytes_to_var(self.aggregate[9:13]))
					val2 = self.bytes_to_var(self.aggregate[13:14], dtU8)
					self.assign_sval(self.ch2Val_scode, self.bytes_to_var(self.aggregate[14:18]))
					val3 = self.bytes_to_var(self.aggregate[18:19], dtU8)
					val4 = self.bytes_to_var(self.aggregate[19:])
					logging.info(' unknown vals?:(%s)' % [val1,val2,val3,val4])
				self.aggregate = bytearray()
		else:  # receiving ordinary nodes
			rec,idx = tls.lookup_lod(self.cmd_tree, scode=shortcode)
			sval = ''.join('{:02x}'.format(x) for x in cValue)
			if rec is None:
				logging.error('unknown node scode:%d val:%s' % (shortcode,sval))
				self.aggregate = bytearray()
				return
			dtType = dtTypes[rec['ntype']]
			logging.info('data:%s (cumlen:%d) from %s(%d) t:%s' % (sval,len(self.aggregate),rec['node'],shortcode,dtType[2]))
			if dtType[0]==0: # unknown len (over 1 or more blocks?)
				expected_len = self.aggregate[1] + self.aggregate[2]*255 + 3
				if len(self.aggregate) >= expected_len:
					if rec['ntype']==dtSTR:
						self.assign_sval(shortcode, self.bytes_to_var(self.aggregate[3:], dtSTR))
					elif rec['ntype']==dtBIN:
						vals = struct.iter_unpack('f',self.aggregate[6:])
						logging.error('unknown sc:%d, v:%s' % (shortcode,','.join('{:}'.format(x) for x in vals)))
					self.aggregate = bytearray() # release memory
			else:
				if rec['ntype'] in (dtU8,dtU16,dtU32,dtS8,dtS16,dtS32,dtCHOOSER,dtFLT):
					self.assign_sval(shortcode, self.bytes_to_var(self.aggregate[1:dtType[0]+1],rec['ntype']))
					logging.info('rcved scode(%d):%s ntype:%d:%s' % (shortcode,self.snode_vals[shortcode],rec['ntype'],dtType))
				else:
					logging.info('rec scode:%d ntype:%d:%s' % (rec['scode'],rec['ntype'],dtType))
				self.aggregate = bytearray() # release memory

	
	def assign_sval(self, scode, sval):
		self.snode_vals[scode] = sval
		if scode in self.snode_callbacks.keys():
			self.snode_callbacks[scode](sval,scode)	

	def _parse_cmd_tree(self):
		""" build command tree from the meter
		"""
		expected_len = self.aggregate[1] + self.aggregate[2]*255 + 3
		if len(self.aggregate) >= expected_len:
			bytes = zlib.decompress(self.aggregate[3:])
			self.aggregate = bytearray() # release memory
			self.seq_n = None
			self.cmd_tree=[]
			crc32 = binascii.crc32(bytes) &  0xffffffff # not finding correct value here !!!
			shortcode = -1
			i=0
			while i<len(bytes):
				ntype = bytes[i]
				nlen  = bytes[i+1]
				name  = bytes[i+2:i+2+nlen].decode('ascii')
				n_children = bytes[i+2+nlen]
				i += 3+nlen
				rec =dict(scode=-1, node=name, nchilds=n_children, ntype=ntype)
				if ntype>1:
					shortcode += 1
					rec['scode']=shortcode
					self.snode_vals[shortcode]=None	
				self.cmd_tree.append(rec)	
			logging.info('tree done %d crc:%0x' % (i,crc32))
			crc32= 0x14795c4a # this one according to intrum
			self.send_cmd('ADMIN:CRC32',crc32)
			return True
		else:
			return False

	def _lookup_node(self, nodeName):
		if ':' in nodeName:
			nodes = nodeName.split(':')
		else:
			nodes = [nodeName]
		endp,idx = self._walk_tree(nodes,1)
		return endp		
	
	def _walk_tree(self,nodes,idx):
		""" find nodes in command tree. nodes must be list [<parentname>,<childname>,...]
		"""
		i=idx
		while i<len(self.cmd_tree):
			rec = self.cmd_tree[i]
			if rec['node']==nodes[0]:
				if len(nodes)==1:
					return rec,i
				return self._walk_tree(nodes[1:],i+1) # look in childs
			else:
				for c in range(rec['nchilds']):
					crec,i = self._walk_tree(['dum'],i+1)
			if nodes[0]=='dum':
				return None,i
			i+=1
		return None,i
		
		
	#def get_nodes(self, scode):
	#	rec,idx = tls.lookup_lod(self.cmd_tree, scode=shortcode)		

	def print_command_tree(self,idx=0,lev=0):
		""" prints available commands, that have been received from the meter 
			including parameter type and shortcodes and childs and value to the console
		"""
		i=idx	
		nbase=self.cmd_tree[idx]['nchilds']
		for r in range(nbase):
			i+=1
			rec = self.cmd_tree[i]
			nchilds = rec['nchilds']
			item ='  '*(lev) + rec['node']
			if rec['scode'] in self.snode_vals.keys():
				val = self.snode_vals[rec['scode']]
			else:
				val='?'
			print('-- %s c:%d sc:%d i:%d v:%s t:%s' % (item.ljust(18),nchilds,rec['scode'],i,val,dtTypes[rec['ntype']][2]))
			if nchilds>0:
				i += self.print_command_tree(i,lev+1)
		return i-idx
					
	def send_cmd_string(self,cmdstr):
		""" sends a commmand to the instrument. the cmdstr must be composed as <parent>:<child> 
			where parent and child must be pairs in the command tree
			Payload can be specified at end separated with space
		"""
		if ' ' in cmdstr:
			cmd = cmdstr.split(' ')[0]
			Payload=float(cmdstr.split(' ')[1])
		else:
			cmd = cmdstr
			Payload=None
		self.send_cmd(cmd, Payload)
								
	def send_cmd(self,nodeName,PayLoad=None):
		""" sends a commmand to the instrument. the cmdstr must be composed as <parent>:<child> 
			where parent and child must be pairs in the command tree
			Payload can be either None:request node value; bytes type; int; float	(depending on ntype of node)
		"""
		rec = self._lookup_node(nodeName)
		scode = rec['scode']
		ntype = rec['ntype']
		dtType = dtTypes[ntype]
		nbytes = dtType[0]
		if scode<0:
			logging.error('ERROR node not a command :%s' % nodeName)
		else:
			if PayLoad is None:
				cmd = bytearray((0,scode))
				logging.info('requesting node value %s(%d)' % (nodeName,scode))
			elif type(PayLoad) == bytes:
				cmd = bytearray((0,scode + 0x80 )) + PayLoad				
			elif ntype >= dtCHOOSER:
				bytesValue = self.var_to_bytes(PayLoad,ntype)
				cmd = bytearray((0,scode + 0x80 )) + bytesValue[-nbytes:]
				sval = ''.join('{:02x}'.format(x) for x in bytesValue[-nbytes:])
				logging.info('send payload %s to %s(%d) dt:%s' % (sval,nodeName,scode,dtType))
			self.cbDelg.write_characteristic(SERIN, bytes(cmd))		
			time.sleep(0.1)
	
	def var_to_bytes(self,var,ntype=dtU8):
		if ntype is None:
			if type(var)==float:
				ntype=dtFLT
			elif type(var==int):
				ntype=dtS32
			elif type(var)==string:
				ntype=dtSTR
		if type(var) == float and ntype != dtFLT:
			var=int(var)
		return struct.pack(dtTypes[ntype][3],var)
		
	def bytes_to_var(self,bytes,ntype=dtFLT):
		if ntype==dtSTR:
			return bytes.decode('ascii')
		if len(bytes)<dtTypes[ntype][0]:
			logging.error('bad bytes len: %d for ntype:%s' % (len(bytes),dtTypes[ntype]))
			if ntype==dtFLT:
				return float('nan')
			return None
		return struct.unpack(dtTypes[ntype][3],bytes)[0]
		
	def get_values(self, scodes=None):
		if scodes is None:
			scodes = (self.ch1Val_scode,self.ch2Val_scode)
		return [self.snode_vals[sc] for sc in scodes]

	def set_results_callback(self, scode, cb):
		logging.info('set_results_callback %s for %d' % (cb,scode))
		self.snode_callbacks[scode] = cb
					
if __name__ == "__main__":
	tls.set_logger(filename='mooshi.log')
	meter = MooshimeterDevice('FB55')       # ('FB55') is my meter (can be omitted for yours)
	time.sleep(2)
	if False:
		meter.send_cmd('REBOOT',0)
		time.sleep(2)
		quit()
	meter.send_cmd('SAMPLING:TRIGGER',0)    # Trigger off	
	print('utc s %d' % int(tls.seconds_since_epoch()))
		
	meter.send_cmd('SAMPLING:RATE',0)       # Rate 125Hz	#
	meter.send_cmd('SAMPLING:DEPTH', 3)     # Depth 256
	meter.send_cmd('CH1:MAPPING',1)         # CH1 select temperature input
	meter.send_cmd('CH1:RANGE_I', 0)        # CH1 350K, 10A range
	meter.send_cmd('CH1:ANALYSIS', 0)       # mean 
	#meter.send_command('CH1:MEAN', 0)         # 
	
	meter.send_cmd('CH2:MAPPING', 2)        # CH2 select shared input
	meter.send_cmd('SHARED', 1)             # CH2 select resistance
	meter.send_cmd('CH2:ANALYSIS', 0)          # mean 
	meter.send_cmd('LOG:ON', 0)              # logging off
	meter.send_cmd('LOG:INTERVAL')          # ms/1000
	
	#meter.send_cmd('SAMPLING:DEPTH', 2)
	meter.send_cmd('CH2:RANGE_I')           # CH2 resitance 1000 range
	meter.send_cmd('CH2:MAPPING')           # get CH2 mapping
	meter.send_cmd('CH2:OFFSET')            # GET OFFSET ?
	meter.send_cmd('ADMIN:DIAGNOSTIC')
	meter.send_cmd('CH2:BUF_BPS')           # bytes per sample
	meter.send_cmd('CH2:BUF_LSB2NATIVE')    # 
	meter.send_cmd('TIME_UTC')
	time.sleep(1)                           # wait for command callbacks filling snode values
	meter.print_command_tree()
	
	def rslt_callback(val, scode):
		print('v %f' % val)
	meter.set_results_callback(meter.ch1Val_scode, rslt_callback)
	meter.set_results_callback(meter.ch2Val_scode, rslt_callback)
	
	print('starting measurement')
	meter.send_cmd('SAMPLING:TRIGGER',2)    # Trigger continuous 
	time.sleep(0.1)
	meter.send_cmd('CH1:VALUE')
	meter.send_cmd('CH2:VALUE')
	for i in range(40):
		time.sleep(0.5)
	meter.send_cmd('SAMPLING:TRIGGER',0)
	time.sleep(3)
	meter.close()
	print('bye')
	logging.shutdown()
