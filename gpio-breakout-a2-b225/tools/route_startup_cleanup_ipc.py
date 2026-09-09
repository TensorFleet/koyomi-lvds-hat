"""Complete startup routing after placement cleanup; keep existing data copper."""
import json,math,sys
from update_addon_ipc import session,D
from route_addon_ipc import copper
from native_astar import _astar_multilayer
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();nets={n.name:n for n in b.get_nets()};fps={f.reference_field.text.value:f for f in b.get_footprints()};out=[]
 def pad(r,n):
  p=next(p for p in fps[r].definition.pads if p.number==str(n));return p.position.x/1e6,p.position.y/1e6
 def route(n,a,z,width=.25,gl=3):
  path=_astar_multilayer(b,n,a,z,layers=(3,34,5),width_mm=width,via_diameter_mm=.5,step=.1,goal_layer=gl,clearance_mm=.21,start_layer=3,board_bounds=(50.65,112.85,50.65,81.35),max_states=250000,via_clearance_mm=.21,via_endpoint_keepout_mm=.7)
  copper(b,nets[n],path,width);out.append({'net':n,'path':path,'width':width});b.save();print(n,'routed',flush=True)
 for n,points in [('USB_SLEW_CT',[pad('U4',4),pad('C3',1)]),('USB_VBUS_IN',[pad('F2',2),pad('U4',1),pad('U4',3),pad('C1',1)]),('USB_VBUS_SOFT',[pad('U4',6),pad('C4',1),pad('U1',1)])]:
  for a,z in zip(points,points[1:]):
   if "--ground-only" not in sys.argv:route(n,a,z,width=.2 if n=='USB_SLEW_CT' else .25)
 # Route to existing ground vias; do not place unscreened new holes.
 gvs=[(v.position.x/1e6,v.position.y/1e6) for v in b.get_vias() if v.net.name=='GND']
 for ref in ['U4','C1','C3','C4']:
  a=pad(ref,2);done=False
  for z in sorted(gvs,key=lambda z:math.dist(a,z))[:8]:
   try:route('GND',a,z,width=.2,gl=3);done=True;break
   except RuntimeError:continue
  assert done,(ref,'GND could not route')
 b.refill_zones();b.save();(D/'reports/startup-routing.json').write_text(json.dumps(out,indent=2)+'\n')
