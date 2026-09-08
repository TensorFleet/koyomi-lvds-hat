"""Exact pad exits avoid snapping sub-millimeter connector rows onto a search grid."""
import json,math
from update_addon_ipc import session,D
from native_astar import _astar_multilayer
from route_addon_ipc import copper
from kipy.geometry import Vector2
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();nets={n.name:n for n in b.get_nets()};fps={f.reference_field.text.value:f for f in b.get_footprints()};out=[]
 def add(net,p,width=.2):copper(b,nets[net],p,width)
 f=fps['C2'];f.position=Vector2.from_xy_mm(96,58);b.update_items([f]);add('USB_VBUS',[(94.725,56.5,3),(94.725,57.5,3),(95.225,58,3)])
 exits={'A9':[(105.83,60,3),(104.8,60,3),(104.3,59.5,3),(104.3,59.5,34)],'A4':[(105.83,63,3),(104.8,63,3),(104.8,63.7,3),(104.8,63.7,34)],'A5':[(105.83,62.5,3),(104.8,62.5,3),(104.2,63.1,3),(104.2,63.1,5)],'B5':[(107.13,60.75,3),(107.7,60.75,3),(108.1,60.3,3),(109.7,60.3,3),(109.7,60.3,5)]}
 for n,p in exits.items():add(next(pad.net.name for pad in fps['J3'].definition.pads if pad.number==n),p)
 add('GND',[(104.7,61.5,3),(104.7,61.5,4)])
 todo=[('USB_CC1',(104.2,63.1),5,(102.45,64.725),3),('USB_CC2',(109.7,60.3),5,(103.15,64.725),3),('USB_VBUS_RAW',(102.9,52.4),3,(104.3,59.5),34),('USB_VBUS_RAW',(104.3,59.5),34,(104.8,63.7),34),('USB_VBUS_RAW',(104.8,63.7),34,(108.2,62.75),3)]
 for net,a,al,z,zl in todo:
  try:
   path=_astar_multilayer(b,net,a,z,layers=(3,5,34),width_mm=.2,via_diameter_mm=.5,step=.1,goal_layer=zl,clearance_mm=.21,start_layer=al,board_bounds=(50.65,112.85,50.65,81.35),max_states=200000,via_clearance_mm=.21,via_endpoint_keepout_mm=.7);add(net,path);out.append(dict(net=net,path=path))
  except RuntimeError as e:out.append(dict(net=net,error=str(e)))
  print(out[-1],flush=True);b.save()
 b.refill_zones();b.save();(D/'reports/usb2-closure.json').write_text(json.dumps(out,indent=2)+'\n')
