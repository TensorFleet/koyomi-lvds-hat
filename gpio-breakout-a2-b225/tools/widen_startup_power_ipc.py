"""Conservatively widen existing power paths through IPC; native DRC is mandatory."""
import json,math,hashlib
from update_addon_ipc import session,D
from native_astar import _layer_obstacles,_distance_to_segment
POWER={'USB_VBUS_IN','USB_VBUS_SOFT'}
p=D/'gpio_breakout.kicad_pcb';before=hashlib.sha256(p.read_bytes()).hexdigest();changes=[];unchanged=[]
with session(p) as k:
 b=k.get_board();tracks=[t for t in b.get_tracks() if t.net.name in POWER];cache={}
 for t in tracks:
  a=(t.start.x/1e6,t.start.y/1e6);z=(t.end.x/1e6,t.end.y/1e6);length=math.dist(a,z);chosen=t.width/1e6
  for width in (.5,.45,.4,.35,.3,.25):
   if width<=chosen:break
   key=(t.net.name,t.layer,width)
   if key not in cache:cache[key]=_layer_obstacles(b,t.layer,t.net.name,width,clearance=.205)
   segs,circles,rects=cache[key];ok=True
   for i in range(max(1,math.ceil(length/.05))+1):
    n=max(1,math.ceil(length/.05));x=a[0]+(z[0]-a[0])*i/n;y=a[1]+(z[1]-a[1])*i/n
    if any(_distance_to_segment(x,y,ax,ay,bx,by)<r for ax,ay,bx,by,r in segs) or any(math.hypot(x-cx,y-cy)<r for cx,cy,r in circles) or any(x0<=x<=x1 and y0<=y<=y1 for x0,y0,x1,y1 in rects):ok=False;break
   if ok:chosen=width;break
  row={'id':t.id.value,'net':t.net.name,'layer':t.layer,'length_mm':length,'before_mm':t.width/1e6,'after_mm':chosen,'start':a,'end':z}
  if chosen>t.width/1e6:t.width=round(chosen*1e6);changes.append(row)
  else:unchanged.append(row)
 b.update_items(tracks)
 b.refill_zones();b.save()
result={'before_sha256':before,'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'target_mm':.5,'clearance_screen_mm':.205,'widened':changes,'retained_necks':unchanged,'status':'candidate pending native DRC and voltage-drop assessment'}
(D/'reports/startup-width-qualification.json').write_text(json.dumps(result,indent=2)+'\n');print('Widened',len(changes),'segments; retained',len(unchanged),'segments for clearance.')
