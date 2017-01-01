import cbBLE
import tls
import time
import zlib
import binascii
import struct

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
	dtU16    :(2,False,'U16',    'H'),
	dtU32    :(4,False,'U32',    'I'),
	dtS8     :(1,True,'S8',      'b'),
	dtS16    :(2,True,'S16',     'h'),
	dtS32    :(4,True,'S32',     'i'),
	dtSTR    :(0,False,'STR',    's'),
	dtBIN    :(0,False,'BIN'),
	dtFLT    :(4,True,'FLT',     'f')
	}

lgSTATE = {
	0:"OK",
	1:"No SD card detected",
	2:"SD card failed to mount - check filesystem",
	3:"SD card is full",
	4:"SD card write error",
	5:"END OF FILE" }

class MooshiMeterDevice (object):
	""" interface to the mooshimeter multimeter using bluetooth on pythonista
	"""
		
	def __init__(self, periph_uid=None):
		""" search for mooshimeter devices with periph_uid in their peripheral UUID code
			gets command tree from the instrument and prints it to the console
		"""
		PerfName='Mooshi'
		lod = [{cbBLE.chPERF:PerfName, cbBLE.chID:i, cbBLE.chPUID:periph_uid, cbBLE.chCUID:None} 
			for i in (SERIN,SEROUT)]	
		lod[SERIN][cbBLE.chCUID] = 'FFA1' 
		lod[SEROUT][cbBLE.chCUID] = 'FFA2'
		self.cbDelg = cbBLE.discover_BLE_characteristics(lod)
		self.cbDelg.setup_response(SEROUT,self._receive_node_callback)
		self.cbDelg.write_characteristic(SERIN, bytes([0x00,0x01])) # request command tree
		self.aggregate = bytearray()
		self.seq_n =None
		self.cmd_tree = []
		self.snode_vals ={}
		self.ch1Val_scode = self.ch2Val_scode = None
		#self.ch1val = self.ch2val = float('NaN')
		
	def close(self):
		self.cbDelg.close()

	def _receive_node_callback(self,cValue):
		seq_n = cValue[0] & 0xFF
		if self.seq_n is not None and seq_n != (self.seq_n+1)%0x100:
			print ('Received out of order packet! Expected:%d, got:%d' % (self.seq_n+1, seq_n))
		self.seq_n = seq_n
		self.aggregate += cValue[1:] # append block and strip sequence number
		shortcode=self.aggregate[0]
		if shortcode==1: # receiving tree, unknown lod yet
			if self._parse_cmd_tree():
				self.ch1Val_scode = self._lookup_node('CH1:VALUE')['scode']
				self.ch2Val_scode = self._lookup_node('CH2:VALUE')['scode']
				self.snode_vals[self.ch1Val_scode]=float('nan')
				self.snode_vals[self.ch2Val_scode]=float('nan')
				print('received tree items:%d ch1Val_scode:%d' % (len(self.cmd_tree),self.ch1Val_scode))
				self.print_command_tree()
		else:  # receiving ordinary nodes
			rec,idx = tls.lookup_lod(self.cmd_tree, scode=shortcode)
			sval = ''.join('{:02x}'.format(x) for x in cValue)
			if rec is None:
				print('unknown node scode:%d val:%s' % (shortcode,sval))
				self.aggregate = bytearray()
				return
			dtType = dtTypes[rec['ntype']]
			print('data:%s (cumlen:%d) from %s(%d) t:%s' % (sval,len(self.aggregate),rec['node'],shortcode,dtType[2]))
			if dtType[0]==0: # unknown len (over 1 or more blocks?)
				expected_len = self.aggregate[1] + self.aggregate[2]*255 + 3
				if len(self.aggregate) >= expected_len:
					if rec['ntype']==dtSTR:
						print('STR:%s' % self.aggregate[3:].decode('ascii'))
					elif rec['ntype']==dtBIN:
						vals = struct.iter_unpack('f',self.aggregate[6:])
						print(','.join('{:}'.format(x) for x in vals))
					self.aggregate = bytearray() # release memory
			else:							
				if rec['ntype']==dtFLT: # it is a float type
					if len(self.aggregate[1:]) != dtType[0]: # bad length
						fVal = float('NaN')
					else:
						fVal = struct.unpack(dtType[3],self.aggregate[1:])[0]
					self.snode_vals[shortcode]=fVal
					#print('other FLT:%f' % fVal)
					print('RSLT %s=%f ch2=%f' % ('ch1',self.snode_vals[self.ch1Val_scode],self.snode_vals[self.ch2Val_scode]))
				elif rec['ntype'] in (dtU8,dtU16,dtU32,dtS8,dtS16,dtS32,dtCHOOSER) and len(self.aggregate[1:]) == dtType[0]:
					self.snode_vals[shortcode] = struct.unpack(dtType[3],self.aggregate[1:])[0]
					print('rcved scode(%d):%d ntype:%d:%s' % (rec['scode'],self.snode_vals[shortcode],rec['ntype'],dtType))
				else:
					print('rec scode:%d ntype:%d:%s' % (rec['scode'],rec['ntype'],dtType))
				self.aggregate = bytearray() # release memory


	def _parse_cmd_tree(self):
		"""
		"""
		expected_len = self.aggregate[1] + self.aggregate[2]*255 + 3
		if len(self.aggregate) >= expected_len:
			#print('done  len:%d ' % (expected_len))
			bytes = zlib.decompress(self.aggregate[3:])
			self.aggregate = bytearray() # release memory
			self.seq_n = None
			self.cmd_tree=[]
			crc32 = binascii.crc32(bytes) # not finding correct value here !!!
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
				#print(rec)
				self.cmd_tree.append(rec)	
			print('tree done %d crc:%0x' % (i,crc32))
			crc32= 0x4a5c7914 # this is the expected value
			self.send_command('ADMIN:CRC32',struct.pack('>I',crc32)) 
			#self.send_command('ADMIN:CRC32',crc32)
			return True
		else:
			return False

	def _lookup_node(self, nodeName):
		if ':' in nodeName:
			nodes = nodeName.split(':')
		else:
			nodes = [nodeName]
		#print('looking for nodes:%s' % nodes)
		endp,idx = self._walk_tree(nodes,1)
		#print('node %d found' % endp['scode'])
		return endp		
	
	def _walk_tree(self,nodes,idx):
		"""
		"""
		i=idx
		while i<len(self.cmd_tree):
			rec = self.cmd_tree[i]
			if rec['node']==nodes[0]:
				if len(nodes)==1:
					#print('node walk %s found at idx %d' % (nodes,i))
					return rec,i
				return self._walk_tree(nodes[1:],i+1) # look in childs
			else:
				for c in range(rec['nchilds']):
					crec,i = self._walk_tree(['dum'],i+1)
			if nodes[0]=='dum':
				return None,i
			i+=1
		return None,i

	def print_command_tree(self,idx=0,lev=0):
		""" prints available commands, including parameter type and shortcodes and childs to the console
		"""
		i=idx	
		nbase=self.cmd_tree[idx]['nchilds']
		for r in range(nbase):
			i+=1
			rec = self.cmd_tree[i]
			nchilds = rec['nchilds']
			item ='  '*(lev) + rec['node']
			print('-- %s c:%d sc:%d i:%d t:%s' % (item.ljust(18),nchilds,rec['scode'],i,dtTypes[rec['ntype']][2]))
			if nchilds>0:
				i += self.print_command_tree(i,lev+1)
		return i-idx
					
	def send_cmd(self,cmdstr,Payload=None):
		""" sends a commmand to the instrument. the cmdstr must be composed as <parent>:<child> 
			where parent and child must be pairs in the command tree
		"""
		if ' ' in cmdstr:
			cmd = cmdstr.split(' ')[0]
			Payload=val(cmdstr.split(' ')[1])
		else:
			cmd = cmdstr
		self.send_command(cmd, Payload)
								
	def send_command(self,nodeName,PayLoad=None):
		"""
		"""
		print('type %s' % type(PayLoad))
		rec = self._lookup_node(nodeName)
		scode = rec['scode']
		ntype = rec['ntype']
		dtType = dtTypes[ntype]
		nbytes = dtType[0]
		if scode<0:
			print('ERROR node not a command :%s' % nodeName)
		else:
			if PayLoad is None:
				cmd = bytearray((0,scode))
				print('requesting node value %s(%d)' % (nodeName,scode))
			elif type(PayLoad) == bytes:
				cmd = bytearray((0,scode + 0x80 )) + PayLoad
			elif ntype >= dtCHOOSER:
				if ntype==dtSTR:
					pass
				bytesValue = self.var_to_bytes(PayLoad,ntype)
				cmd = bytearray((0,scode + 0x80 )) + bytesValue[-nbytes:]
				sval = ''.join('{:02x}'.format(x) for x in bytesValue[-nbytes:])
				print('send payload %s to %s(%d) dt:%s' % (sval,nodeName,scode,dtType))
			self.cbDelg.write_characteristic(SERIN, bytes(cmd))		
			time.sleep(1)
	
	def var_to_bytes(self,num,ntype=dtU8):
		if ntype is None:
			if type(num)==float:
				ntype=dtFLT
			elif type(num==int):
				ntype=dtS32
			elif type(num)==string:
				ntype=dtSTR
		return struct.pack(dtTypes[ntype][3],num)
		
if __name__=="__main__":
	meter = MooshiMeterDevice('FB55')       # ('FB55') is my meter (can be omitted)
	time.sleep(2)
	if False:
		meter.send_cmd('REBOOT',0)
		time.sleep(2)
		quit()
	meter.send_cmd('SAMPLING:TRIGGER',0)     # Trigger off	
	print('utc s %d' % int(tls.timedelta_since().total_seconds()))
	meter.send_cmd('TIME_UTC', int(tls.timedelta_since().total_seconds()))     # 
	
	meter.send_cmd('SAMPLING:RATE',0)       # Rate 125Hz	#
	meter.send_cmd('SAMPLING:DEPTH', 3)     # Depth 256
	meter.send_cmd('CH1:MAPPING',1)         # CH1 select temperature input
	meter.send_cmd('CH1:RANGE_I', 0)         # CH1 350K, 10A range
	meter.send_cmd('CH1:ANALYSIS', 0)          # mean 
	#meter.send_cmd('CH2:MAPPING', 0)         # CH2 select voltage input
	
	meter.send_cmd('CH2:MAPPING', 2)         # CH2 select shared input
	meter.send_cmd('SHARED', 1)             # CH2 select resistance
	meter.send_cmd('CH2:ANALYSIS', 0)          # mean 
	meter.send_cmd('LOG:ON', 0)              # logging off
	
	meter.send_cmd('SAMPLING:DEPTH', 2)
	meter.send_cmd('CH2:RANGE_I')           # CH2 resitance 1000 range
	meter.send_cmd('CH2:MAPPING')           # get CH2 mapping
	meter.send_cmd('CH2:OFFSET')            # GET OFFSET ?
	meter.send_cmd('ADMIN:DIAGNOSTIC')
	#meter.send_cmd('CH2:BUF')               #
	#meter.send_cmd('LOG:INTERVAL')          # ms/1000
	meter.send_cmd('TIME_UTC')     
	time.sleep(1)
	print('starting measurement')
	meter.send_cmd('SAMPLING:TRIGGER',2)       #Trigger continuous 
	time.sleep(0.1)
	for i in range(20):
		meter.send_cmd('CH1:VALUE')
		#time.sleep(.3)
		meter.send_cmd('CH2:VALUE')
		#meter.send_cmd('SAMPLING:TRIGGER',2)   # Trigger once
		for i in range(1):
			time.sleep(0.5)
	for i in range(4):
		time.sleep(4)
	meter.send_cmd('SAMPLING:TRIGGER',0)
	time.sleep(5)
	meter.close()
	print('bye')
