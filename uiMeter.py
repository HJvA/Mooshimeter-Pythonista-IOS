import ui
import Mooshimeter
import tls
import time

tls.set_logger()

def update_results(results):
	print('results %s %s' % (vrslt['rsltVal1'].text,results))
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
		
class vwGraph(ui.View):
	def did_load(self):
		pass
				
meter = Mooshimeter.Mooshimeter('FB55')  # 'FB55' is my meter
time.sleep(2)
meter.set_results_callback(update_results)
meter.trigger(Mooshimeter.trModes['continuous'])

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
