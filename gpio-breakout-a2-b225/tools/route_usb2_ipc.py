"""Coupled USB2 route and bounded ordinary-net completion using native IPC.

Main pair is offset from one centreline, never independently searched. Each
reversible connector B contact has two regular .50/.30 through transitions.
Native DRC and endpoint audits are required after this candidate is generated.
"""
import json,math
from update_addon_ipc import session,D
from route_addon_ipc import copper
from native_astar import _astar_multilayer
from kipy.geometry import Vector2,Angle

def offset(points,d):
 normals=[]
 for a,b in zip(points,points[1:]):
  dx,dy=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dy);normals.append((-dy/l,dx/l))
 out=[(points[0][0]+d*normals[0][0],points[0][1]+d*normals[0][1])]
 for i,p in enumerate(points[1:-1],1):
  a,b=normals[i-1],normals[i];den=1+a[0]*b[0]+a[1]*b[1]
  out.append((p[0]+d*(a[0]+b[0])/den,p[1]+d*(a[1]+b[1])/den))
 out.append((points[-1][0]+d*normals[-1][0],points[-1][1]+d*normals[-1][1]));return out

def main():
 report={'routes':[],'removed':[]}
 with session(D/'gpio_breakout.kicad_pcb') as k:
  b=k.get_board();old=json.loads((D/'reports/usb2-coupled-candidate.json').read_text());remove=set(old.get('new_copper_uuids',[]));b.remove_items([x for x in [*b.get_tracks(),*b.get_vias()] if x.id.value in remove]);nets={n.name:n for n in b.get_nets()};before={x.id.value:x.proto.SerializeToString().hex() for x in [*b.get_tracks(),*b.get_vias()]}
  fps={f.reference_field.text.value:f for f in b.get_footprints()}
  for ref,xy,angle in [('U2',(102.6,61.5),90),('F2',(101.5,52.4),180),('U1',(96,52.4),0),('C1',(99,56),0),('C2',(95.5,56.5),0),('R1',(98.5,65.5),0),('R2',(102,66),0),('U3',(102.8,64.3),0)]:
   f=fps[ref];f.orientation=Angle.from_degrees(angle);f.position=Vector2.from_xy_mm(*xy);b.update_items([f])
  def add(net,pts,width=.2,layer=3):
   pts=[(*p,layer) if len(p)==2 else p for p in pts];copper(b,nets[net],pts,width);report['routes'].append(dict(net=net,path=pts,width=width))
  center=[(88,55.23),(88,56.8),(91.2,60),(99.5,60),(100.5,61),(100.8,61)]
  for net,d,first,last in [('USB_D_P',.2,(87.75,55.23),(103.025,61.85)),('USB_D_N',-.2,(88.25,55.23),(103.025,61.15))]:
   fan=[(101.1,62.15),(102.9,62.15),last] if d>0 else [(101.1,60.7),(102.9,60.7),last]
   add(net,[first]+offset(center,d)+fan)
  add('USB_D_P',[(103.025,61.85),(104.5,61.85),(104.8,62),(105.83,62)])
  add('USB_D_N',[(103.025,61.15),(104.5,61.15),(104.8,61),(105.83,61)])
  add('USB_D_P',[(107.13,61.25,3),(107.8,61.25,3),(108.1,61.1,3),(108.1,61.1,5),(106.7,61.1,5),(105.8,62,5),(103.8,62,5),(103.8,62,3),(104.8,62,3)])
  add('USB_D_N',[(107.13,61.75,3),(108.7,61.75,3),(108.7,61.75,5),(108.7,59.9,5),(104.9,59.9,5),(103.8,61,5),(103.8,61,3),(104.8,61,3)])
  add('GND',[(102.175,61.5,3),(101.8,61.5,3),(101.8,61.5,4)])
  add('GND',[(109.7,61.5,3),(109.7,61.5,4)])
  add('USB_VBUS',[(89.25,55.23),(90.75,55.23),(92.75,55.23),(94.02,56.5),(94.725,56.5)],.25)
  b.save();(D/'reports/usb2-coupled-candidate.json').write_text(json.dumps(report,indent=2)+'\n')
  # Existing continuous ground pours connect decouplers; add screened stitches later.
  # Each non-data net uses a deterministic minimum-distance spanning tree.
  for name in ('USB_CC1','USB_CC2','USB_VBUS_RAW','USB_VBUS_IN','USB_VBUS'):
   pads=[(f.reference_field.text.value,p) for f in b.get_footprints() for p in f.definition.pads if p.net.name==name]
   if name=='USB_VBUS':pads=[x for x in pads if x[0]!='J1' or x[1].number=='4']
   connected=[pads[0]];pending=pads[1:]
   while pending:
    _,a,c=min((math.dist((p.position.x,p.position.y),(q.position.x,q.position.y)),(r,p),(s,q)) for r,p in connected for s,q in pending)
    start=(a[1].position.x/1e6,a[1].position.y/1e6);end=(c[1].position.x/1e6,c[1].position.y/1e6)
    try:
     path=_astar_multilayer(b,name,start,end,layers=(3,5,34),width_mm=.2,via_diameter_mm=.5,step=.1,goal_layer=3,clearance_mm=.21,start_layer=3,board_bounds=(50.65,112.85,50.65,81.35),max_states=200000,via_clearance_mm=.21,via_endpoint_keepout_mm=.7)
     add(name,path);print(name,a[0],a[1].number,c[0],c[1].number,'routed',flush=True)
    except RuntimeError as e:
     report['routes'].append(dict(net=name,from_pad=[a[0],a[1].number],to_pad=[c[0],c[1].number],error=str(e)));print(str(e),flush=True)
    connected.append(c);pending.remove(c);b.save();(D/'reports/usb2-coupled-candidate.json').write_text(json.dumps(report,indent=2)+'\n')
  after={x.id.value:x.proto.SerializeToString().hex() for x in [*b.get_tracks(),*b.get_vias()]}
  assert all(after.get(i)==v for i,v in before.items()),'Prior LCD copper changed'
  report['preserved_prior_copper_count']=len(before);report['new_copper_uuids']=sorted(set(after)-set(before))
  b.refill_zones();b.save();(D/'reports/usb2-coupled-candidate.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
