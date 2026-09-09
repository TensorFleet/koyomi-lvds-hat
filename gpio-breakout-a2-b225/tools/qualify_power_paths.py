"""DC trace-path upper bounds from native geometry, with explicit nonqualification limits."""
import heapq,json,math
from pathlib import Path
D=Path(__file__).resolve().parents[1];r=json.loads((D/'reports/qualification-native-snapshot.json').read_text())
LAYERS=['BL_F_Cu','BL_In1_Cu','BL_In2_Cu','BL_B_Cu'];DEPTH=[0,.2355,1.3157,1.5512];THICK=[.035,.0152,.0152,.035];RHO=1.7241e-5

def xy(p):return tuple(round(int(p.get(v,0))/1e6,6) for v in ('x_nm','y_nm'))
def dist(p,a,b):
 dx=b[0]-a[0];dy=b[1]-a[1];l=dx*dx+dy*dy;t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/l)) if l else 0
 return math.dist(p,(a[0]+t*dx,a[1]+t*dy))
pads={}
for ref,f in r['footprints'].items():
 for p in f['definition']['items']:
  if p['@type'].endswith('.Pad') and p.get('number'):pads[ref,p['number']]=p

def graph(net):
 ts=[t for t in r['tracks'] if t.get('net',{}).get('name')==net];vs=[v for v in r['vias'] if v.get('net',{}).get('name')==net]
 nodes=set();pn={}
 for key,p in pads.items():
  if p.get('net',{}).get('name')!=net:continue
  ls=[l for l in p['pad_stack']['layers'] if l in LAYERS];pn[key]=[(*xy(p['position']),l) for l in ls];nodes.update(pn[key])
 for t in ts:nodes.update([(*xy(t['start']),t['layer']),(*xy(t['end']),t['layer'])])
 for v in vs:nodes.update([(*xy(v['position']),l) for l in LAYERS])
 g={n:[] for n in nodes}
 def edge(a,b,res,length=0,via=False):g[a].append((b,res,length,via));g[b].append((a,res,length,via))
 for t in ts:
  a,b=xy(t['start']),xy(t['end']);ns=[n for n in nodes if n[2]==t['layer'] and dist(n[:2],a,b)<.00002];ns.sort(key=lambda n:math.dist(a,n[:2]));width=int(t['width']['value_nm'])/1e6;thick=THICK[LAYERS.index(t['layer'])]
  for u,v in zip(ns,ns[1:]):
   length=math.dist(u[:2],v[:2]);edge(u,v,RHO*length/(width*thick),length)
 for v in vs:
  d=int(v['pad_stack']['drill']['diameter']['x_nm'])/1e6;ns=[(*xy(v['position']),l) for l in LAYERS]
  for i,(u,z) in enumerate(zip(ns,ns[1:])):edge(u,z,RHO*(DEPTH[i+1]-DEPTH[i])/(math.pi*d*.020),0,True)
 for ns in pn.values():
  # PTH barrel resistance omitted: separately accounted as contact/terminal losses.
  for u,z in zip(ns,ns[1:]):edge(u,z,0)
 return g,pn

def path(start,finish):
 net=pads[start]['net']['name'];assert pads[finish]['net']['name']==net
 g,pn=graph(net);q=[(0,n) for n in pn[start]];cost={n:0 for n in pn[start]};prev={};goal=None
 while q:
  d,n=heapq.heappop(q)
  if d!=cost[n]:continue
  if n in pn[finish]:goal=n;break
  for z,res,length,via in g[n]:
   nd=d+res
   if nd<cost.get(z,1e99):cost[z]=nd;prev[z]=(n,length,via);heapq.heappush(q,(nd,z))
 assert goal is not None,(start,finish,net)
 n=goal;length=0;vias=set()
 while n in prev:
  z,l,v=prev[n];length+=l
  if v:vias.add(n[:2])
  n=z
 rr=cost[goal];return {'from':start,'to':finish,'net':net,'single_path_resistance_ohm_20C':rr,'single_path_resistance_ohm_60C':rr*(1+.00393*40),'path_length_mm':length,'through_vias':len(vias),'drop_V_at_100mA_60C':rr*1.1572*.1,'drop_V_at_500mA_60C':rr*1.1572*.5}
def main():
 queries=[(('J3','A4'),('F2','1')),(('F2','2'),('U4','1')),(('U4','6'),('U1','1')),(('U1','6'),('J1','1')),(('J2','2'),('JP4','1')),(('JP4','2'),('F1','1')),(('F1','2'),('J1','9')),(('J2','1'),('JP5','1')),(('JP5','2'),('J1','11'))]
 rows=[path(a,b) for a,b in queries];usbR=sum(row['single_path_resistance_ohm_60C'] for row in rows[:4]);ptc=.75
 out={'source_board_sha256':r['board_sha256'],'method':'Shortest-resistance continuous conductor path, using saved copper thicknesses; ignoring parallel copper gives a conservative bound for the modeled positive path. Not a bound on complete assembled loop loss.','assumptions':{'copper_resistivity_ohm_mm':RHO,'via_wall_mm_assumed_unverified':.020,'temperature_C':60,'PTC_resistance_ohm_screen':ptc},'paths':rows,'USB_positive_copper_bound_ohm_60C':usbR,'USB_positive_copper_plus_PTC_drop_V':{str(i):i*(usbR+ptc) for i in (.1,.25,.5)},'excluded_losses':['TPS22918','LM66100','USB cable','FFC cable and connector contacts','PTH terminal resistance','ground return','downstream board'],'scope':'Low-power bench only. F2 is a PTC, not a regulated current limiter. No full USB-A load or host enumeration/inrush qualification.','inrush':{'C1_direct_downstream_nominal_uF':120.2,'charge_at_5V_uC':601,'mean_capacitive_current_A_by_rise_ms':{str(t):120.2e-6*5/(t/1000) for t in (.1,1,5,10)},'controlled_startup':'TPS22918 before LM66100, ON tied to input, QOD unconnected, CT 10 nF C0G 50 V 5%', 'typical_10_90_rise_ms_at_5V':26.55, 'typical_10_90_capacitive_current_mA':120.2e-6*4/.02655*1000, 'result':'Controlled startup implemented; typical calculation is not a guaranteed peak-current limit. Validate host droop and actual startup/load current on assembled hardware.'}}
 (D/'reports/power-path-qualification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))

if __name__=='__main__':main()
