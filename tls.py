import struct

def populate_lod(lod, csv_fp, fields=['id','name']):
	'''
	'''
	rdr = csv.DictReader(csv_fp, fields)
	lod.extend(rdr)

def query_lod(lod, filter=None, sort_keys=None):
	'''
	pprint(query_lod(lod, sort_keys=('Priority', 'Year')))
	print len(query_lod(lod, lambda r:1997 <= int(r['Year']) <= 2002))
	print len(query_lod(lod, lambda r:int(r['Year'])==1998 and int(r['Priority']) > 2))
	'''
	if filter is not None:
		lod = (r for r in lod if filter(r))
	if sort_keys is not None:
		lod = sorted(lod, key=lambda r:[r[k] for k in sort_keys])
	else:
		lod = list(lod)
	return lod

def lookup_lod(lod, **kw):
	'''
	pprint(lookup_lod(lod, Row=1))
	pprint(lookup_lod(lod, Name='Aardvark'))
	'''
	i=0
	for row in lod:
		for k,v in kw.items():
			if row[k] != v:   
				i += 1
				break #next row
		else:
			return row,i
	return None,-1

def num_to_bytes(num): 
	""" not good
	"""
	if num is None:
		return None
	elif type(num) == float:
		return struct.unpack("BBBB",struct.pack("f",num))
	else:
		rs = bytearray()
		if type(num) == int:	
			return struct.pack('>I',num)		
			for i in range(4):
				rs.append(num & 0xFF)
				num >>= 8
		else:
			# Is it iterable?  Try it, assuming it's a list of bytes
			for byte in num:
				rs.append(byte)
		return rs
		
	def _bytes_to_num(bytes, b=1,t=int,signed=False):
		# not used
		i=0
		if t == int:
			if b > len(bytes):
				print('not enough bytes for INT')
				#raise UnderflowException()
			r = 0
			s = 0
			top_b = 0
			while b:
				top_b = bytes[i]
				r += top_b << s
				s += 8
				i += 1
				b -= 1
			# Sign extend
			if signed and top_b & 0x80:
				r -= 1 << s
			return r
		elif t==float:
			if 4 > len(bytes):
				print('not enough bytes for FLT')
			r = struct.unpack("f",struct.pack("BBBB",*bytes[i:i+4]))
			i += 4
			return r[0]

