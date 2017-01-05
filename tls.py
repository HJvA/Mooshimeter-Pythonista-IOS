#import struct
import datetime
import logging

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

def timedelta_since(dtStart=datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)):
	''' time in s since 1970-1-1 midnight utc
	'''
	return  datetime.datetime.now(tz=datetime.timezone.utc) -dtStart
			
def console_logger():
	# define a Handler which writes INFO messages or higher to the sys.stderr
	console = logging.StreamHandler()
	console.setLevel(logging.NOTSET)
	# set a format which is simpler for console use
	formatter = logging.Formatter('%(levelname)-8s %(message)s')
	# tell the handler to use this format
	console.setFormatter(formatter)
	# add the handler to the root logger
	logger = logging.getLogger()
	logger.handlers = []
	logger.addHandler(console)
	return logger

if __name__ == "__main__":
	print('seconds since 1-1-1970 : %s' % int(timedelta_since().total_seconds()))
