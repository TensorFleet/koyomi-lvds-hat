"""Close native DRC opens by reusing existing escaped through vias."""
import json
from update_addon_ipc import session,D
from native_astar import _astar_multilayer
from route_addon_ipc import copper
report=json.loads((D/'reports/drc.json').read_text());results=[]
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();nets={n.name:n for n in b.get_nets()};fps={f.reference_field.text.value:f for f in b.get_footprints()}
 for finding in report['unconnected_items']:
  net=finding['items'][0]['description'].split('[')[1].split(']')[0];v=next(v for v in b.get_vias() if v.net.name==net);q=next(p for p in fps['J2'].definition.pads if p.net.name==net);origin=(v.position.x/1e6,v.position.y/1e6);goal=(q.position.x/1e6,q.position.y/1e6);done=False
  for layer in [34,5,3]:
   try:
    path=_astar_multilayer(b,net,origin,goal,layers=(34,5,3),width_mm=.2,via_diameter_mm=.5,step=.1,goal_layer=None,clearance_mm=.23,start_layer=layer,board_bounds=(50.65,112.85,50.65,81.35),max_states=350000,via_clearance_mm=.23,via_endpoint_keepout_mm=.7)
    count=copper(b,nets[net],path);b.save();results.append(dict(net=net,items=count,layer=layer));done=True;break
   except RuntimeError as e:print(net,layer,str(e),flush=True)
  if not done:results.append(dict(net=net,status='pending'))
 b.refill_zones();b.save()
(D/'reports/closure.json').write_text(json.dumps(results,indent=2)+'\n');print(results)
