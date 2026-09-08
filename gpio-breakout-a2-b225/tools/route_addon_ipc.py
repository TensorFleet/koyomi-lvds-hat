"""Bounded obstacle-aware routing via native KiCad IPC, followed by DRC."""
import json,math,time
from kipy.board_types import Track,Via,ViaType
from kipy.geometry import Vector2
from update_addon_ipc import session,D
from native_astar import _astar_multilayer

def copper(b,net,path,width=.2):
 items=[]
 for p,q in zip(path,path[1:]):
  if p[2]!=q[2]:
   v=Via();v.position=Vector2.from_xy_mm(*p[:2]);v.type=ViaType.VT_THROUGH;v.padstack.drill.start_layer=3;v.padstack.drill.end_layer=34;v.diameter=500000;v.drill_diameter=300000;v.net=net;items.append(v)
  elif math.dist(p[:2],q[:2])>1e-6:
   t=Track();t.start=Vector2.from_xy_mm(*p[:2]);t.end=Vector2.from_xy_mm(*q[:2]);t.width=round(width*1e6);t.layer=p[2];t.net=net;items.append(t)
 before={i.id.value for i in [*b.get_tracks(),*b.get_vias()]};b.create_items(items)
 live=[i for i in [*b.get_tracks(),*b.get_vias()] if i.id.value not in before]
 for i in live:i.net=net
 b.update_items(live)
 return len(live)

def main():
 results=[]
 with session(D/'gpio_breakout.kicad_pcb') as k:
  b=k.get_board();b.remove_items(list(b.get_tracks())+list(b.get_vias()));nets={n.name:n for n in b.get_nets()};fps=b.get_footprints();by_net={}
  for f in fps:
   for p in f.definition.pads:
    if p.net.name:by_net.setdefault(p.net.name,[]).append((f.reference_field.text.value,p))
  # Stitch ground contacts into the retained inner plane. Short tails leave
  # the Samtec land row toward the board interior, never the aperture side.
  for ref,p in by_net['GND']:
   if ref=='J2':continue
   x,y=p.position.x/1e6,p.position.y/1e6
   if ref=='J1':path=[(x,y,3),(x,y-1.5,3),(x,y-1.5,4)]
   else:path=[(x,y,3),(x+.9,y,3),(x+.9,y,4)]
   copper(b,nets['GND'],path,.2)
  # Reserve a spaced through-via fanout for every LCD contact. Maximum
  # divergence is below 33 degrees, maintaining the inherited .20 mm rules.
  exits={}
  for f in fps:
   if f.reference_field.text.value=='J1':
    for p in f.definition.pads:
     if p.net.name and p.net.name!='GND':
      x,y=p.position.x/1e6,p.position.y/1e6;n=int(p.number);vx=81+(20.5-n)*.8;vy=66.2+(n%2)
      copper(b,nets[p.net.name],[(x,y,3),(x,56.2,3),(vx,65.5,3),(vx,vy,3),(vx,vy,5)])
      exits[p.number]=(vx,vy)
  # Route short nets first; each source sees existing native copper as obstacles.
  work=[]
  for net,pads in by_net.items():
   if net=='GND' or len(pads)<2:continue
   connected=[pads[0]];remaining=pads[1:]
   while remaining:
    _,a,c=min((math.dist((p.position.x,p.position.y),(q.position.x,q.position.y)),(r,p),(s,q)) for r,p in connected for s,q in remaining)
    work.append((math.dist((a[1].position.x,a[1].position.y),(c[1].position.x,c[1].position.y)),net,a,c));connected.append(c);remaining.remove(c)
  work.sort(key=lambda w:w[0])
  for _,net,(ref,p),(ref2,q) in work:
   start=(p.position.x/1e6,p.position.y/1e6);goal=(q.position.x/1e6,q.position.y/1e6)
   sl=3;gl=None if ref2=='J2' else 3
   # A PTH header supports starting from either outer or inner signal layer.
   if ref=='J2':sl=34
   origin=start
   if ref=='J1':origin=exits[p.number];sl=5;start=origin
   goalroute=goal
   if ref2=='J1':goalroute=exits[q.number];gl=5;goal=goalroute
   try:
    path=_astar_multilayer(b,net,origin,goalroute,layers=(3,34,5),width_mm=.2,via_diameter_mm=.5,step=.15,goal_layer=gl,clearance_mm=.21,start_layer=sl,board_bounds=(50.65,112.85,50.65,81.35),max_states=200000,via_clearance_mm=.21,via_endpoint_keepout_mm=.7)
    if origin!=start:path=[(*start,3)]+path
    if goalroute!=goal:path=path+[(*goal,3)]
    count=copper(b,nets[net],path);results.append(dict(net=net,from_ref=ref,to_ref=ref2,status='routed',items=count));b.save()
   except RuntimeError as e:results.append(dict(net=net,status='pending',reason=str(e)))
   print(results[-1],flush=True);(D/'reports/route-pass.json').write_text(json.dumps(results,indent=2)+'\n')
  b.refill_zones();b.save()
 print('Routing candidate complete; native DRC required')
if __name__=='__main__':main()
