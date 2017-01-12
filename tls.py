#import struct
import datetime
import logging
import os

def populate_lod(lod, csv_fp, fields=['id','name']):
	''' get list of dict from csv file
	'''
	rdr = csv.DictReader(csv_fp, fields)
	lod.extend(rdr)

def query_lod(lod, filter=None, sort_keys=None):
	''' get list of dict filtered from lod
	pprint(query_lod(lod, sort_keys=('Priority', 'Year')))
	print len(query_lod(lod, lambda r:1997 <= int(r['Year']) <= 2002))
	print len(query_lod(lod, lambda r:int(r['Year'])==1998 and int(r['Priority']) > 2))
	'''
	if filter is not None:
		lod = (r for r in lod if filter(r))
	if sort_keys is not None:
		lod = sorted(lod, key=lambda r: [r[k] for k in sort_keys])
	else:
		lod = list(lod)
	return lod

def lookup_lod(lod, **kw):
	''' get first dict from lod with key value
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

def seconds_since_epoch(epoch = datetime.datetime.utcfromtimestamp(0), dtnow=datetime.datetime.utcnow()):
	''' time in s since 1970-1-1 midnight utc
	'''
	return (dtnow - epoch).total_seconds()
			
def set_logger(filename=None, format='%(levelname)-6s %(message)s', level=logging.NOTSET):
	formatter = logging.Formatter(format)
	'''
	'''
	if filename is None:
		hand = logging.StreamHandler() # console
	else:
		hand = logging.FileHandler(filename=filename, mode='w')
	hand.setLevel(level)
	hand.setFormatter(formatter)
	logger = logging.getLogger()
	[logger.removeHandler(h) for h in logger.handlers[::-1]]
	logger.addHandler(hand)
	return hand
	

if __name__ == "__main__":
	#set_logger(level=logging.INFO)
	logging.basicConfig(level=logging.NOTSET)
	print('lev %s' % logging.getLogger().handlers[0].level)
	logging.info('hallo wereld')
	logging.warning(os.getcwd())
	logging.error(os.getlogin())
	print('seconds since epoch : %s' % seconds_since_epoch())
	logging.shutdown()
