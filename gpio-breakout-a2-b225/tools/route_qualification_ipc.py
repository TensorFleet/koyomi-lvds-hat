"""Route the new startup and source-series circuits with native obstacle geometry.

Preserves each existing FFC escape up to its first via and leaves USB data
copper untouched. Search results remain candidates until native DRC and audits.
"""
import copy,json,math,sys
from pathlib import Path
from update_addon_ipc import session,D
from qualification_design import ARRAYS,DRIVEN
from route_addon_ipc import copper
from native_astar import _astar_multilayer
from kipy.geometry import Vector2,Angle
from kipy.board_types import Track,Via
key=lambda v:(round(v.x/1e6,5),round(v.y/1e6,5))
base=Path(sys.argv[1]);escapes={};items=[]
with session(base) as k:
 b=k.get_board();j=next(f for f in b.get_footprints() if f.reference_field.text.value=='J1')
 for p in j.definition.pads:
  n=p.net.name
  if n not in DRIVEN:continue
  ts=[t for t in b.get_tracks() if t.net.name==n and t.layer==3];vs={key(v.position):v for v in b.get_vias() if v.net.name==n};at=key(p.position);seen=set();travel=0
  while at not in vs and travel<4:
   opts=[t for t in ts if t.id.value not in seen and at in (key(t.start),key(t.end))]
   assert len(opts)==1,(n,at,len(opts))
   t=opts[0];seen.add(t.id.value);next_at=key(t.end) if at==key(t.start) else key(t.start);travel+=math.dist(at,next_at);items.append(Track(proto=copy.deepcopy(t.proto)));at=next_at
  if at in vs:items.append(Via(proto=copy.deepcopy(vs[at].proto)));escapes[n]=(at,5)
  else:escapes[n]=(at,3)
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();nets={n.name:n for n in b.get_nets()}
 for f in b.get_footprints():
  ref=f.reference_field.text.value
  if ref in ARRAYS:
   f.orientation=Angle.from_degrees(270);f.position=Vector2.from_xy_mm(f.position.x/1e6,75)
   f.reference_field.text.position=Vector2.from_xy_mm(f.position.x/1e6,77.8);b.update_items([f])
 for item in items:item.net=nets[item.net.name]
 b.create_items(items);b.save()
 results=[]
 def route(n,a,z,sl=3,gl=3,width=.2,layers=(3,34,5)):
  try:
   path=_astar_multilayer(b,n,a,z,layers=layers,width_mm=width,via_diameter_mm=.5,step=.1,goal_layer=gl,clearance_mm=.21,start_layer=sl,board_bounds=(50.65,112.85,50.65,81.35),max_states=220000,via_clearance_mm=.21,via_endpoint_keepout_mm=.7)
   copper(b,nets[n],path,width);r={'net':n,'status':'routed','path':path,'width':width}
  except RuntimeError as e:r={'net':n,'status':'pending','from':a,'to':z,'error':str(e)}
  results.append(r);b.save();(D/'reports/qualification-route-pass.json').write_text(json.dumps(results,indent=2)+'\n');print(n,r['status'],flush=True)
 fps={f.reference_field.text.value:f for f in b.get_footprints()}
 def pad(ref,num):return key(next(p for p in fps[ref].definition.pads if p.number==str(num)).position)
 # Power signal tree; .50 mm on unconstrained routes, .20–.25 pin escape.
 for n,points in [('USB_SLEW_CT',[pad('U4',4),pad('C3',1)]),('USB_VBUS_IN',[pad('U4',1),pad('U4',3),pad('C1',1),pad('F2',2)]),('USB_VBUS_SOFT',[pad('U4',6),pad('C4',1),pad('U1',1)])]:
  for a,z in zip(points,points[1:]):route(n,a,z,width=.2 if n=='USB_SLEW_CT' else .25)
 # Explicit local ground stitches at the new devices.
 for ref,num,via in [('U4',2,(97.1,56.35)),('C3',2,(103.55,58)),('C4',2,(97.35,54.3)),('C1',2,(104.6,55.5))]:
  a=pad(ref,num);route('GND',a,via,gl=3)
  copper(b,nets['GND'],[(*via,3),(*via,4)])
 # Short Pi-to-array inputs first. Header pins are plated through.
 jobs=[]
 for ref,group in ARRAYS.items():
  for i,n in enumerate(group):
   if not n:continue
   source=next(p for p in fps['J2'].definition.pads if p.net.name==n+'_PI');a=key(source.position);z=pad(ref,i+1)
   jobs.append((math.dist(a,z),n+'_PI',a,z))
 for _,n,a,z in sorted(jobs):route(n,a,z,sl=34)
 # Array-to-FFC outputs terminate on the original spaced via escapes.
 jobs=[]
 for ref,group in ARRAYS.items():
  for i,n in enumerate(group):
   if n:jobs.append((math.dist(pad(ref,8-i),escapes[n][0]),n,pad(ref,8-i),escapes[n][0],escapes[n][1]))
 for _,n,a,z,gl in sorted(jobs):route(n,a,z,gl=gl)
 b.refill_zones();b.save()
 print('Routing pass complete:',sum(r['status']=='pending' for r in results),'pending paths.')
