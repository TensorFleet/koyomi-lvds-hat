"""Repair only remaining GPIO4/5/6 escapes; preserve other verified copper."""
import json
from update_addon_ipc import session,D
from route_addon_ipc import copper
from native_astar import _astar_multilayer
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();names={'GPIO4','GPIO5','GPIO6'};b.remove_items([v for v in [*b.get_tracks(),*b.get_vias()] if v.net.name in names]);nets={n.name:n for n in b.get_nets()};fps={f.reference_field.text.value:f for f in b.get_footprints()};results=[]
 for net in sorted(names):
  p=next(p for p in fps['J1'].definition.pads if p.net.name==net);q=next(p for p in fps['J2'].definition.pads if p.net.name==net)
  start=(p.position.x/1e6,p.position.y/1e6);goal=(q.position.x/1e6,q.position.y/1e6);done=False
  for dist in [2.5]:
   origin=({'GPIO4':80.5,'GPIO5':79.5,'GPIO6':78.5}[net],52.7)
   try:
    path=_astar_multilayer(b,net,origin,goal,layers=(3,34,5),width_mm=.2,via_diameter_mm=.5,step=.1,goal_layer=None,clearance_mm=.27,start_layer=5,board_bounds=(50.65,112.85,50.65,81.35),max_states=250000,via_clearance_mm=.27,via_endpoint_keepout_mm=.7)
    count=copper(b,nets[net],[(*start,3),(start[0],54.2,3),(*origin,3),(*origin,5)]+path);results.append(dict(net=net,items=count,escape_mm=dist));b.save();done=True;break
   except RuntimeError as e:print(net,dist,e,flush=True)
  if not done:raise RuntimeError(net+' remains open')
 b.refill_zones();b.save()
(D/'reports/escape-repair.json').write_text(json.dumps(results,indent=2)+'\n');print(results)
