"""Native endpoint path geometry; does not claim USB impedance/compliance qualification."""
import json,math,heapq
from google.protobuf.json_format import MessageToDict
from update_addon_ipc import session,D

def xy(v):return(round(v.x/1e6,6),round(v.y/1e6,6))
def distance(p,a,b):
 dx,dy=b[0]-a[0],b[1]-a[1];d=dx*dx+dy*dy;t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/d)) if d else 0
 return math.dist(p,(a[0]+t*dx,a[1]+t*dy))
def inside(p,pts):
 c=False
 for a,b in zip(pts,pts[1:]+pts[:1]):
  if ((a[1]>p[1])!=(b[1]>p[1])) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:c=not c
 return c
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();fps={f.reference_field.text.value:f for f in b.get_footprints()};groundvias=[xy(v.position) for v in b.get_vias() if v.net.name=='GND'];out={'stackup':MessageToDict(b.get_stackup().proto,preserving_proto_field_name=True),'paths':[],'data_vias':[],'qualification':'Saved native stack is still generic0.48/0.48/0.48mm dielectric. JLC04161H-7628 is a future process-reference choice; physical stackup update pending. Coplanar ground is interrupted at breakouts/bends; narrow contact joins remain. Uniform impedance, USB enumeration/current and assembled-link signal integrity are not qualified.'}
 for name,ffc,a_pin,b_pin in [('USB_D_P','7','A6','B6'),('USB_D_N','6','A7','B7')]:
  ts=[t for t in b.get_tracks() if t.net.name==name];vs=[v for v in b.get_vias() if v.net.name==name];nodes=set();pads={}
  for f in fps.values():
   for p in f.definition.pads:
    if p.net.name==name:pads[f.reference_field.text.value,p.number]=(*xy(p.position),3)
  nodes.update(pads.values())
  for t in ts:nodes.update([(*xy(t.start),t.layer),(*xy(t.end),t.layer)])
  for v in vs:
   for layer in (3,4,5,34):nodes.add((*xy(v.position),layer))
   pos=xy(v.position);out['data_vias'].append({'net':name,'xy':pos,'diameter_mm':v.diameter/1e6,'drill_mm':v.drill_diameter/1e6,'nearest_gnd_via_mm':min(math.dist(pos,g) for g in groundvias)})
  graph={n:[] for n in nodes}
  def edge(a,z,w,via=False):graph[a].append((z,w,via));graph[z].append((a,w,via))
  for t in ts:
   a,z=xy(t.start),xy(t.end);ns=[n for n in nodes if n[2]==t.layer and distance(n[:2],a,z)<.00002];ns.sort(key=lambda n:math.dist(a,n[:2]))
   for u,v in zip(ns,ns[1:]):edge(u,v,math.dist(u[:2],v[:2]))
  for v in vs:
   ns=[(*xy(v.position),l) for l in (3,4,5,34)]
   for u,z in zip(ns,ns[1:]):edge(u,z,0,True)
  start=pads['J1',ffc]
  for pin in (a_pin,b_pin):
   goal=pads['J3',pin];q=[(0,start)];cost={start:0};prev={}
   while q:
    d,n=heapq.heappop(q)
    if d!=cost[n]:continue
    if n==goal:break
    for z,w,via in graph[n]:
     nd=d+w
     if nd<cost.get(z,1e99):cost[z]=nd;prev[z]=(n,via);heapq.heappush(q,(nd,z))
   assert goal in cost,(name,pin,'disconnected endpoint graph')
   path=[goal];n=goal
   while n!=start:n=prev[n][0];path.append(n)
   path.reverse();usedvias=set(tuple(a[:2]) for a,z in zip(path,path[1:]) if a[2]!=z[2]);layers=sorted(set(n[2] for n in path));out['paths'].append({'net':name,'from':['J1',ffc],'to':['J3',pin],'planar_length_mm':cost[goal],'layers':layers,'routed_copper_layers':sorted({a[2] for a,z in zip(path,path[1:]) if a[2]==z[2] and a[:2]!=z[:2]}),'used_through_vias':len(usedvias),'path':path})
 # Actual reference plane: F.Cu -> In1.Cu; In2.Cu -> B.Cu.
 planes={}
 for z in b.get_zones():
  if z.net.name!='GND':continue
  for layer,filled in z.filled_polygons.items():
   for p in filled:
    outline=[xy(n.point) for n in p.outline if n.has_point];holes=[[xy(n.point) for n in h if n.has_point] for h in p.holes];planes.setdefault(layer,[]).append((outline,holes))
 def ground(p,layer):return any(inside(p,o) and not any(inside(p,h) for h in hs) for o,hs in planes.get(layer,[]))
 samples={3:dict(reference_layer=4,total=0,covered=0,transition_samples_excluded=0,misses=[]),5:dict(reference_layer=34,total=0,covered=0,transition_samples_excluded=0,misses=[])}
 vias=[xy(v.position) for v in b.get_vias() if v.net.name.startswith('USB_D_')];coplanar={'total':0,'covered':0,'missing_samples':[],'sample_offset_beyond_trace_edge_mm':.26}
 data=[t for t in b.get_tracks() if t.net.name.startswith('USB_D_')]
 for t in data:
  a,z=xy(t.start),xy(t.end);length=math.dist(a,z);count=max(1,math.ceil(length/.1));row=samples[t.layer]
  for i in range(count+1):
   p=(a[0]+(z[0]-a[0])*i/count,a[1]+(z[1]-a[1])*i/count)
   if any(math.dist(p,v)<=.501 for v in vias):row['transition_samples_excluded']+=1;continue
   row['total']+=1;good=ground(p,row['reference_layer']);row['covered']+=good
   if not good:row['misses'].append(p)
   if t.layer==3 and t.width==277400 and length>.1:
    normal=(-(z[1]-a[1])/length,(z[0]-a[0])/length);off=t.width/2e6+.26;choices=[(p[0]+sign*off*normal[0],p[1]+sign*off*normal[1]) for sign in (-1,1)];mates=[v for v in data if v.net.name!=t.net.name and v.layer==3];outer=max(choices,key=lambda point:min(distance(point,xy(m.start),xy(m.end)) for m in mates));coplanar['total']+=1;good=ground(outer,3);coplanar['covered']+=good
    if not good:coplanar['missing_samples'].append(outer)
 for row in samples.values():row['all_covered']=row['covered']==row['total'];row['antipad_radius_basis_mm']=.5;row['numerical_polygon_margin_mm']=.001
 out['reference_samples_by_routing_layer']=samples;out['main_pair_coplanar_ground_samples']=coplanar
 for row in ('A','B'):
  pair=[p for p in out['paths'] if p['to'][1].startswith(row)];out[row+'_contact_pair']={'planar_skew_mm':abs(pair[0]['planar_length_mm']-pair[1]['planar_length_mm']),'via_parity':pair[0]['used_through_vias']==pair[1]['used_through_vias']}
 (D/'reports/usb2-path-audit.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k not in ['stackup','paths']});print([(p['to'],p['planar_length_mm'],p['used_through_vias']) for p in out['paths']])
