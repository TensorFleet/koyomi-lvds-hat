import json
from pathlib import Path
from google.protobuf.json_format import MessageToDict
from update_addon_ipc import session,D
from kipy.board_types import Net
from usb2_interface import MAP

def snap(path):
 with session(path) as k:
  b=k.get_board();out={}
  for x in [*b.get_footprints(),*b.get_tracks(),*b.get_vias()]:
   if hasattr(x,'definition'):
    ref=x.reference_field.text.value
    for p in x.definition.pads:p.net=Net(name=MAP['J1'].get(p.number) or '') if ref=='J1' else Net(name=p.net.name)
    key=ref
   else:x.net=Net(name=x.net.name);key=x.id.value
   out[key]=MessageToDict(x.proto,preserving_proto_field_name=True)
  return out

def diff(a,b,p=''):
 if type(a)!=type(b):return [(p,a,b)]
 if isinstance(a,dict):return [d for k in set(a)|set(b) for d in diff(a.get(k),b.get(k),p+'/'+k)]
 if isinstance(a,list):
  if len(a)!=len(b):return [(p+'/length',len(a),len(b))]
  return [d for i,(x,y) in enumerate(zip(a,b)) for d in diff(x,y,p+'/'+str(i))]
 return [] if a==b else [(p,a,b)]
a=snap(Path('/private/tmp/gpio-usb-prior-native.kicad_pcb'));b=snap(D/'gpio_breakout.kicad_pcb');out={key:diff(v,b[key]) for key,v in a.items()};out={k:[d for d in v if not d[0].endswith('/id/value') and d[0]!='/parent/value'] for k,v in out.items()};out={k:v for k,v in out.items() if v};(D/'reports/usb2-preservation-differences.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(list(out.items())[:2]),indent=2))

(D/'reports/usb2-baseline-preservation.json').write_text(json.dumps({'passed':not out,'original_footprints_checked':9,'original_copper_checked':len(a)-9,'allowed_metadata_differences':['native item child IDs','native parent session ID'],'allowed_electrical_changes':['J1 USB pins1-4,6,7 per USB extension'],'unexpected_differences':out},indent=2)+'\n')
