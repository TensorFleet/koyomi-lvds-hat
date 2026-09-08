"""Move only USB_RAW backside tracks away from In2 USB reference footprints.

Temporary native projections screen the ordinary-net search, then are removed
before any board save. They are never retained as physical copper.
"""
import json,math
from update_addon_ipc import session,D
from route_addon_ipc import copper
from native_astar import _astar_multilayer
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();nets={n.name:n for n in b.get_nets()};old=[t for t in b.get_tracks() if t.layer==34 and t.net.name=='USB_VBUS_RAW'];b.remove_items(old);before={x.id.value for x in b.get_tracks()}
 for t in list(b.get_tracks()):
  if t.layer==5 and t.net.name in ('USB_D_P','USB_D_N'):
   copper(b,nets[t.net.name],[(t.start.x/1e6,t.start.y/1e6,34),(t.end.x/1e6,t.end.y/1e6,34)],.3)
 projections={t.id.value for t in b.get_tracks()}-before
 vias=[(v.position.x/1e6,v.position.y/1e6) for v in b.get_vias() if v.net.name=='USB_VBUS_RAW'];connected=[vias[0]];pending=vias[1:];out=[]
 while pending:
  _,a,z=min((math.dist(a,z),a,z) for a in connected for z in pending)
  p=_astar_multilayer(b,'USB_VBUS_RAW',a,z,layers=(34,),width_mm=.2,via_diameter_mm=.5,step=.1,goal_layer=34,clearance_mm=.3,start_layer=34,board_bounds=(50.65,112.85,50.65,81.35),max_states=150000,via_clearance_mm=.3)
  copper(b,nets['USB_VBUS_RAW'],p,.2);out.append(p);connected.append(z);pending.remove(z)
 b.remove_items([t for t in b.get_tracks() if t.id.value in projections]);assert not any(t.id.value in projections for t in b.get_tracks())
 b.refill_zones();b.save();(D/'reports/usb2-vbus-reference-routing.json').write_text(json.dumps({'removed_raw_B_track_uuids':[x.id.value for x in old],'projection_uuids_removed_before_save':sorted(projections),'paths':out},indent=2)+'\n');print('USB_RAW backside routes moved outside data-reference corridors.')
