"""Read-only native evidence for GPIO A2 manufacturing findings."""
import hashlib,json,math
from collections import defaultdict
from google.protobuf.json_format import MessageToDict
from update_addon_ipc import session,D
p=D/'gpio_breakout.kicad_pcb';before=hashlib.sha256(p.read_bytes()).hexdigest()
with session(p) as k:
 b=k.get_board();f=next(f for f in b.get_footprints() if f.reference_field.text.value=='J1')
 power=defaultdict(list)
 for t in b.get_tracks():
  if t.net.name.startswith(('+','USB_VBUS')):power[t.net.name].append({'width_mm':t.width/1e6,'layer':t.layer,'length_mm':math.hypot(t.start.x-t.end.x,t.start.y-t.end.y)/1e6})
 result={'board_sha256':before,'j1':MessageToDict(f.proto,preserving_proto_field_name=True),'j1_pads':[MessageToDict(p.proto,preserving_proto_field_name=True) for p in f.definition.pads],'stackup':MessageToDict(b.get_stackup().proto,preserving_proto_field_name=True),'power_tracks':dict(power),'footprint_values':{f.reference_field.text.value:f.value_field.text.value for f in b.get_footprints()}}
assert before==hashlib.sha256(p.read_bytes()).hexdigest()
(D/'reports/manufacturing-findings-native.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'power_tracks':{n:{'widths':sorted(set(t['width_mm'] for t in ts)),'layers':sorted(set(t['layer'] for t in ts)),'length_mm':sum(t['length_mm'] for t in ts)} for n,ts in power.items()},'j1_first_pad':result['j1_pads'][0],'j1_description':result['j1']['definition']['attributes'].get('description'),'j1_pad_count':len(result['j1_pads'])},indent=2))
