"""Restore custom footprints after import and clear space for startup circuitry."""
import copy,json,sys
from pathlib import Path
from update_addon_ipc import session,sheets,D
from kipy.board_types import FootprintInstance
from kipy.geometry import Vector2,Angle
with session(Path(sys.argv[1])) as k:
 originals={f.reference_field.text.value:FootprintInstance(proto=copy.deepcopy(f.proto)) for f in k.get_board().get_footprints() if f.reference_field.text.value in ('J1','JP4','JP5')}
with session(D/'gpio_breakout.kicad_sch') as k:
 root,ss=sheets(k);paths={f.reference_field.text.value:([v.value for v in s.document.sheet_path.path],f.id.value) for s in ss for f in s.get_symbols()}
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();fps=b.get_footprints();counts={}
 for ref,f in originals.items():
  old=[v for v in fps if v.reference_field.text.value==ref];counts[ref]=len(old);b.remove_items(old)
  del f.proto.symbol_path.path[:]
  for s in paths[ref][0]+[paths[ref][1]]:f.proto.symbol_path.path.add().value=s
  b.create_items([f])
 # Remove only new ground routes by their exact path endpoints.
 routes=json.loads((D/'reports/qualification-route-pass.json').read_text());key=lambda p:tuple(round(v,5) for v in p)
 gkeys={tuple(sorted((key(a),key(z)))) for r in routes if r['net']=='GND' and r['status']=='routed' for a,z in zip(r['path'],r['path'][1:]) if a[2]==z[2]}
 removals=[]
 for t in b.get_tracks():
  ends=tuple(sorted((key((t.start.x/1e6,t.start.y/1e6,t.layer)),key((t.end.x/1e6,t.end.y/1e6,t.layer)))))
  if t.net.name in ('USB_VBUS_IN','USB_VBUS_SOFT','USB_SLEW_CT') or (t.net.name=='GND' and ends in gkeys):removals.append(t)
 for v in b.get_vias():
  if v.net.name in ('USB_VBUS_IN','USB_VBUS_SOFT','USB_SLEW_CT') or (v.net.name=='GND' and key((v.position.x/1e6,v.position.y/1e6)) in {(97.1,56.35),(103.55,58),(97.35,54.3),(104.6,55.5)}):removals.append(v)
 b.remove_items(removals)
 positions={'U4':(106,52.3),'C1':(101,55.5),'C3':(106,55.5),'C4':(100,58)}
 for f in b.get_footprints():
  if f.reference_field.text.value in positions:
   x,y=positions[f.reference_field.text.value];f.position=Vector2.from_xy_mm(x,y);f.reference_field.text.position=Vector2.from_xy_mm(x,y-1.9);b.update_items([f])
 b.refill_zones();b.save();print('Restored custom connector/jumper definitions:',counts,'; moved power additions to clear locations.')
