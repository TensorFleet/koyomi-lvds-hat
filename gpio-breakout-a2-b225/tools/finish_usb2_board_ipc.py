"""Final ground return, route-tail cleanup, readable assembly labels and native preservation audit."""
import json,copy,hashlib
from pathlib import Path
from update_addon_ipc import session,D
from route_addon_ipc import copper
from kipy.board_types import BoardText,BoardLayer,Net
from kipy.geometry import Vector2,Angle
from usb2_interface import MAP
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();nets={n.name:n for n in b.get_nets()};r=json.loads((D/'reports/usb2-escape-drc.json').read_text());ids={i['uuid'] for x in r['violations'] if x['type']=='track_dangling' for i in x['items']};b.remove_items([t for t in b.get_tracks() if t.id.value in ids])
 copper(b,nets['GND'],[(102.825,66,3),(103.725,66,3),(103.725,66,4)])
 labels={'U1':(95.9,54.6),'F2':(101.5,54.4),'C1':(99,57.4),'C2':(96,59.4),'U2':(101.8,59),'U3':(104.2,64.9),'R1':(98.5,64.1),'R2':(102,67.25),'J3':(111,66.9)}
 for f in b.get_footprints():
  ref=f.reference_field.text.value
  if ref not in labels:continue
  field=f.reference_field;field.text.position=Vector2.from_xy_mm(*labels[ref]);field.text.attributes.angle=0;field.text.attributes.size=Vector2.from_xy_mm(.65,.65);field.text.attributes.stroke_width=100000;f.reference_field=field;b.update_items([f])
 for t in b.get_text():
  if t.value=='GPIO LCD A2':t.value='GPIO LCD A2 + USB2';b.update_items([t])
  if t.value.startswith('USB pins'):t.value='USB HOST INPUT / LCD POWER LINKS OPEN';b.update_items([t])
 b.refill_zones();b.save()
# Compare all original native footprint definitions, fields, positions and IDs.
with session(Path('/private/tmp/gpio-usb-prior-native.kicad_pcb')) as k:
 prior={f.reference_field.text.value:f for f in k.get_board().get_footprints()};tracks={x.id.value:x for x in [*k.get_board().get_tracks(),*k.get_board().get_vias()]}
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();current={f.reference_field.text.value:f for f in b.get_footprints()};checks=[]
 for ref,a in prior.items():
  z=current[ref]
  for f in (a,z):
   for p in f.definition.pads:p.net=Net(name=MAP['J1'].get(p.number) or '') if ref=='J1' else Net(name=p.net.name)
  checks.append({'ref':ref,'equal':a.proto.SerializeToString()==z.proto.SerializeToString(),'pad_count':len(z.definition.pads)})
 after={x.id.value:x for x in [*b.get_tracks(),*b.get_vias()]};tc=[]
 for id,a in tracks.items():
  z=after[id];a.net=Net(name=a.net.name);z.net=Net(name=z.net.name);tc.append(a.proto.SerializeToString()==z.proto.SerializeToString())
 out={'footprints':checks,'all_original_footprints_exact':all(x['equal'] for x in checks),'original_copper_count':len(tc),'all_original_copper_exact':all(tc)}
 (D/'reports/usb2-baseline-preservation.json').write_text(json.dumps(out,indent=2)+'\n');print(out)
