"""Widen only the shared USB main pair to the JLC7628 calculator result."""
import json
from update_addon_ipc import session,D
from route_addon_ipc import copper
from route_usb2_ipc import offset

def key(a,z):return tuple(sorted((tuple(round(v,6) for v in a),tuple(round(v,6) for v in z))))
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();nets={n.name:n for n in b.get_nets()};old=json.loads((D/'reports/usb2-coupled-candidate.json').read_text())['routes'][:2];keys={r['net']:{key(a,z) for a,z in zip(r['path'],r['path'][1:])} for r in old};remove=[]
 for t in b.get_tracks():
  if t.net.name in keys and key((t.start.x/1e6,t.start.y/1e6,t.layer),(t.end.x/1e6,t.end.y/1e6,t.layer)) in keys[t.net.name]:remove.append(t)
 b.remove_items(remove);out=[]
 center=[(88,55.23),(88,56.8),(91.2,60),(99.5,60),(100.5,61),(100.8,61)]
 for net,delta,first,last in [('USB_D_P',.2387,(87.75,55.23),(103.025,61.85)),('USB_D_N',-.2387,(88.25,55.23),(103.025,61.15))]:
  paired=[first]+offset(center,delta);fan=[(101.1,62.15),(102.9,62.15),last] if delta>0 else [(101.1,60.7),(102.9,60.7),last]
  copper(b,nets[net],[(*p,3) for p in paired],.2774);copper(b,nets[net],[(*p,3) for p in [paired[-1]]+fan],.2)
  out.append({'net':net,'main_width_mm':.2774,'main_gap_mm':.2,'main':paired,'short_escape_width_mm':.2,'escape':fan})
 b.refill_zones();b.save();(D/'reports/usb2-impedance-route.json').write_text(json.dumps({'removed_main_track_uuids':[x.id.value for x in remove],'routes':out},indent=2)+'\n');print('Updated only main pair; native DRC required.')
