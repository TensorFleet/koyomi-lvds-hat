import json
from google.protobuf.json_format import MessageToDict
from update_addon_ipc import session,D,sheets
with session(D/'gpio_breakout.kicad_sch') as k:
 root,ss=sheets(k)
 for sch in ss:
  for s in sch.get_symbols():
   if s.reference_field.text.value in ('J3','U2','R1'):
    (D/'reports'/('symbol-'+s.reference_field.text.value+'.json')).write_text(json.dumps(MessageToDict(s.proto,preserving_proto_field_name=True),indent=2)+'\n')
