import ui
import dialogs
import Mooshimeter
import multimeter as mm
import tls
import time

print(tls.set_logger())

def update_results(results):
	#print('results %s %s' % (vrslt['rsltVal1'].text,results))
	vrslt['rsltVal1'].text ='%4f'  % results[0]
	vrslt['rsltBar1'].value = (results[0] - 273.15)/100
	vrslt['rsltVal2'].text ='%4f'  % results[1]
	vrslt['rsltBar2'].value = results[1]/200
	
def show_page(sender):
	print('page %s' % sender.selected_index)
	global actPage 
	if actPage is not None:
		vw.remove_subview(actPage)
	if sender.selected_index == 0:
		actPage = vset
	elif sender.selected_index == 1:
		actPage = vrslt
	vw.add_subview(actPage)
	actPage.y =60

def set_function(chan):
	if chan==2:
		keys = Mooshimeter.mooshiFunc2.keys()
	else:
		keys = Mooshimeter.mooshiFunc1.keys()
	nms = [n for n in mm.mmFunctions.keys() if mm.mmFunctions[n] in keys]
	lds =ui.ListDataSource([{'title':tm, 'accessory_type':'detail_button'} for tm in nms]	)
	print([d['title'] for d in lds.items])
	sel =dialogs.list_dialog('select function',lds.items)
	if sel:
		fnc = mm.mmFunctions[sel['title']]
		print('mmfunc:%s(%d)' % (sel, fnc))
		meter.set_function(chan, fnc)
		return sel['title']

def func1act(sender):
	sender.title = set_function(1)

def func2act(sender):
	sender.title = set_function(2)
		
		
	
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
				
meter = Mooshimeter.Mooshimeter('FB55')  # 'FB55' is my meter
time.sleep(2)
meter.set_results_callback(update_results)
meter.meter.print_command_tree()
meter.trigger(mm.trModes['continuous'])

actPage=None
vw = ui.load_view()
vw['selPage'].action = show_page
vset = ui.load_view('mm_settings.pyui')
vrslt = ui.load_view('mm_results.pyui')

if min(ui.get_screen_size()) >= 768:
	# iPad
	vw.frame = (0, 0, 360, 500)
	vw.present('sheet')
else:
	# iPhone
	vw.present(orientations=['portrait'])

print('bye')
