import json
from update_addon_ipc import session,D
from route_addon_ipc import copper
from native_astar import _astar_multilayer
from kipy.geometry import Vector2
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();nets={n.name:n for n in b.get_nets()};remove=[]
 for t in b.get_tracks():
  a=(t.start.x/1e6,t.start.y/1e6);z=(t.end.x/1e6,t.end.y/1e6)
  if t.net.name=='USB_VBUS_RAW' and (min(a[0],z[0])>=107 or (a==(104.8,63.0) and z==(104.8,63.7)) or (a==(105.83,63.0) and z==(104.8,63.0))):remove.append(t)
 for v in b.get_vias():
  if (v.net.name=='GND' and abs(v.position.x/1e6-104.7)<.001) or (v.net.name=='USB_VBUS_RAW' and v.position.x/1e6>=107):remove.append(v)
 b.remove_items(remove)
 def add(n,p):copper(b,nets[n],p)
 add('GND',[(103,60.05,3),(103,60.05,4)]);add('GND',[(103,62.8,3),(103,62.8,4)])
 add('USB_VBUS_RAW',[(105.83,63,3),(105,63,3),(105,63.9,3),(104.8,63.9,3),(104.8,63.7,3)])
 add('USB_VBUS_RAW',[(107.13,60.25,3),(107.7,60.25,3),(109.05,58.9,3),(109.5,58.9,3),(109.5,58.9,34)])
 add('USB_VBUS_RAW',[(107.13,62.75,3),(108.75,62.75,3),(109,63,3),(109,63,34)])
 out=[]
 for a,z in [((109.5,58.9),(104.3,59.5)),((109,63),(104.8,63.7))]:
  path=_astar_multilayer(b,'USB_VBUS_RAW',a,z,layers=(34,),width_mm=.2,via_diameter_mm=.5,step=.1,goal_layer=34,clearance_mm=.21,start_layer=34,board_bounds=(50.65,112.85,50.65,81.35),max_states=100000,via_clearance_mm=.21);add('USB_VBUS_RAW',path);out.append(path)
 b.refill_zones();b.save();(D/'reports/usb2-clearance-repair.json').write_text(json.dumps({'removed':[x.id.value for x in remove],'routes':out},indent=2)+'\n')
