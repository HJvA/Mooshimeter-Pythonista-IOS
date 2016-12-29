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

dtTypes = {	# (nBytes, Signed, Name)
	dtPLAIN  :(0,False,'PLAIN'),
	dtLINK   :(0,False,'LINK'),
	dtCHOOSER:(1,False,'CHOOSER'),
	dtU8     :(1,False,'U8'),
	dtU16    :(2,False,'U16'),
	dtU32    :(4,False,'U32'),
	dtS8     :(1,True,'S8'),
	dtS16    :(2,True,'S16'),
	dtS32    :(4,True,'S32'),
	dtSTR    :(0,False,'STR'),
	dtBIN    :(0,False,'BIN'),
	dtFLT    :(4,True,'FLT')
	}

class MooshiMeterDevice (object):
	"""
	"""
		
	def __init__(self, periph_uid=None):
		"""
		"""
		PerfName='Mooshi'
		lod = [{cbBLE.chPERF:PerfName, cbBLE.chID:i, cbBLE.chPUID:periph_uid, cbBLE.chCUID:None} 
			for i in (SERIN,SEROUT)]	
		lod[SERIN][cbBLE.chCUID] = 'FFA1' 
		lod[SEROUT][cbBLE.chCUID] = 'FFA2'
		self.cbDelg = cbBLE.discover_BLE_characteristics(lod)
		self.cbDelg.write_characteristic(SERIN, bytes([0x00,0x01])) # request command tree
		self.cbDelg.setup_response(SEROUT,self._receive_node_callback)
		self.aggregate = bytearray()
		self.seq_n =None
		self.cmd_tree = []
		self.ch1Val_scode = self.ch2Val_scode = None
		self.ch1val = self.ch2val = float('NaN')
		
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
				print('received tree items:%d ch1Val_scode:%d' % (len(self.cmd_tree),self.ch1Val_scode))
				self.print_command_tree()
		else:  # receiving ordinary nodes
			rec,idx = tls.lookup_lod(self.cmd_tree, scode=shortcode)
			sval = ''.join('{:02x}'.format(x) for x in cValue)
			if rec is None:
				print('unknown node scode:%d val:%s' % (shortcode,sval))
				return
			dtType = dtTypes[rec['ntype']]
			print('data:%s (cumlen:%d) from %s(%d) t:%s' % (sval,len(self.aggregate),rec['node'],shortcode,dtType[2]))
			if dtType[0]==0: # unknown len (over 1 or more blocks?)
				expected_len = self.aggregate[1] + self.aggregate[2]*255 + 3
				if len(self.aggregate) >= expected_len:
					print('STR:%s' % self.aggregate[3:].decode('ascii'))
					self.aggregate = bytearray() # release memory
			else:							
				if rec['ntype']==dtFLT: # it is a float type
					fVal = struct.unpack('f',self.aggregate[1:])[0]
					if shortcode==self.ch1Val_scode:
						self.ch1val=fVal
					elif shortcode==self.ch2Val_scode:
						self.ch2val=fVal
					print('RSLT %s=%f ch2=%f' % ('ch1',self.ch1val,self.ch2val))
				else: # todo
					print('rec scode:%d ntype:%d' % (rec['scode'],rec['ntype']))
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
				#print(rec)
				self.cmd_tree.append(rec)	
			print('tree done %d crc:%0x' % (i,crc32))
			crc32= 0x4a5c7914 
			self.send_command('ADMIN:CRC32',struct.pack('>I',crc32)) 
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
		"""
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
					
	def send_cmd(self,cmdstr,NumPayload=None):
		"""
		"""
		if ' ' in cmdstr:
			cmd = cmdstr.split(' ')[0]
			NumPayload=val(cmdstr.split(' ')[1])
		else:
			cmd = cmdstr
		self.send_command(cmd, tls.num_to_bytes(NumPayload))
								
	def send_command(self,nodeName,bytesValue=None):
		"""
		"""
		rec = self._lookup_node(nodeName)
		scode = rec['scode']
		ntype = rec['ntype']
		dtType = dtTypes[ntype]
		nbytes = dtType[0]
		if bytesValue is None:
			cmd = bytearray((0,scode))
			sval = None
		else:
			cmd = bytearray((0,scode + 0x80 )) + bytesValue[-nbytes:]
			sval = ''.join('{:02x}'.format(x) for x in bytesValue[-nbytes:])
		print('send payload %s to %s(%d) dt:%s' % (sval,nodeName,scode,dtType))
		self.cbDelg.write_characteristic(SERIN, bytes(cmd))		
	
if __name__=="__main__":
	meter = MooshiMeterDevice('FB55')       # ('FB55') is my meter : can be omitted
	time.sleep(2)
	#meter.send_cmd('SAMPLING:RATE',0)       # Rate 125Hz
	#meter.send_cmd('SAMPLING:DEPTH', 3)     # Depth 256
	meter.send_cmd('CH1:MAPPING',1)         # CH1 select temperature input
	meter.send_cmd('CH1:RANGE_I', 0)         # CH1 350K, 10A range
	#meter.send_cmd('CH2:MAPPING', 0)         # CH2 select voltage input
	meter.send_cmd('CH2:MAPPING', 2)         # CH2 select shared input
	meter.send_cmd('SHARED', 1)             # CH2 select resistance
	meter.send_cmd('CH2:RANGE_I')           # CH2 resitance 1000 range
	meter.send_cmd('CH2:MAPPING')           # get CH2 mapping
	#meter.send_cmd('SHARED:RESISTANCE')     # GET resistance range ?
	meter.send_cmd('ADMIN:DIAGNOSTIC')
	meter.send_cmd('CH2:ANALYSIS')           # 
	meter.send_cmd('SAMPLING:TRIGGER',0)     # Trigger continuous ?
	meter.send_cmd('SAMPLING:TRIGGER',2)       #
	
	time.sleep(1)
	for i in range(10):
		meter.send_cmd('CH1:VALUE')
		meter.send_cmd('CH2:VALUE')
		meter.send_cmd('PCB_VERSION')   # Trigger once
		time.sleep(1)
	meter.close()
	print('bye')
