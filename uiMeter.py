""" main user entry point for mooshimeter bluetooth multimeter """
import ui
import dialogs
from pymooshi import Mooshimeter
from pymooshi.genlibpy import  multimeter as mm
from pymooshi.genlibpy import tls
import time

print(tls.set_logger())

def update_results(results):
	vrslt['rsltVal1'].text ='%4f'  % results[0]
	vrslt['rsltBar1'].value = results[0]/meter.ch_targets[0]  #  (results[0] - 273.15)/100
	vrslt['rsltVal2'].text ='%4f'  % results[1]
	vrslt['rsltBar2'].value = results[1]/meter.ch_targets[1]
	
def show_page(page_idx, pages):
	print('page %s/%d' % (page_idx,len(vw.subviews)))
	global actPage 
	if actPage is None:
		for pg in pages:
			pg.hidden=True
			pg.y=60
			pg.flex='WH'
			vw.add_subview(pg)
		fill_function(1)
		fill_function(2)
	else:
		actPage.hidden=True
		#vw.remove_subview(actPage)
	actPage = pages[page_idx]
	actPage.hidden=False
		
	
def fill_function(chan, mmFunction=None):
	if mmFunction is None:
		mmFunction = meter.get_mmFunction(chan)
	vset['function%d' % chan].title = mm.mmFunctions[mmFunction][0]
	vrslt['unit%d' % chan].text = mm.mmFunctions[mmFunction][1]
	vset['target%d' % chan].text = '%.1f' % meter.ch_targets[chan-1]
	print('u%d:%s' % (chan,vrslt['unit%d' % chan].text))
	

def set_function(chan):
	if chan==2:
		keys = Mooshimeter.mooshiFunc2.keys()
	else:
		keys = Mooshimeter.mooshiFunc1.keys()
	nms = [mm.mmFunctions[k][0] for k in mm.mmFunctions.keys() if k in keys]
	lds =ui.ListDataSource([{'title':tm} for tm in nms]	)
	print([d['title'] for d in lds.items])
	sel =dialogs.list_dialog('select function',lds.items)
	if sel:
		fnc = mm.mmFunction(sel['title'])
		trg = float(vset['target%d' % chan].text)
		print('mmfunc:%s(%d) trg:%f' % (sel, fnc, trg))
		meter.set_function(chan, fnc, trg)
		fill_function(chan,fnc)
		return sel['title']

def func1act(sender):
	sender.title = set_function(1)

def func2act(sender):
	sender.title = set_function(2)		

def selPageAct(sender):
	page = sender.selected_index
	show_page(page,(vset,vrslt))
		
	
class vwMultimeter(ui.View):
	def did_load(self):
		pass
	def will_close(self):
		print('closing')
		meter.trigger(0)
		meter.close()

class vwSettings(ui.View):
	def did_load(self):
		pass
		
class vwResults(ui.View):
	def did_load(self):
		pass
		
class vwGraph(ui.View):
	def did_load(self):
		pass
				
meter = Mooshimeter.Mooshimeter()  # 'FB55' is my meter
time.sleep(2)
meter.set_results_callback(update_results)
meter.meter.print_command_tree()
meter.trigger(mm.trModes['continuous'])

actPage=None
vw = ui.load_view()
#vw.flex = 'WH'
vw['selPage'].action = selPageAct
vset = ui.load_view('mm_settings.pyui')
vrslt = ui.load_view('mm_results.pyui')
show_page(0,(vset,vrslt))

if min(ui.get_screen_size()) >= 768:
	# iPad
	vw.frame = (0, 0, 500, 600)
	vw.present('sheet')
else:
	# iPhone
	vw.present(orientations=['portrait'])

print('bye')
