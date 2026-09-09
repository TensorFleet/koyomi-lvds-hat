"""Source-bound native geometry snapshot for electrical qualification."""
import json,hashlib,sys
from pathlib import Path
from google.protobuf.json_format import MessageToDict
from update_addon_ipc import session,D
p=Path(sys.argv[1]) if len(sys.argv)>1 else D/'gpio_breakout.kicad_pcb'
with session(p) as k:
 b=k.get_board();out={'board_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'footprints':{f.reference_field.text.value:MessageToDict(f.proto,preserving_proto_field_name=True) for f in b.get_footprints()},'tracks':[MessageToDict(x.proto,preserving_proto_field_name=True) for x in b.get_tracks()],'vias':[MessageToDict(x.proto,preserving_proto_field_name=True) for x in b.get_vias()],'stackup':MessageToDict(b.get_stackup().proto,preserving_proto_field_name=True)}
(D/'reports/qualification-native-snapshot.json').write_text(json.dumps(out,indent=2)+'\n')
print({k:len(v) for k,v in out.items() if k in ['footprints','tracks','vias']})
