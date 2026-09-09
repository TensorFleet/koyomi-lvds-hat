"""Check unrelated copper and original physical connectors against the baseline."""
import json,sys,hashlib
from pathlib import Path
from update_addon_ipc import session,D
from qualification_design import DRIVEN

def capture(p):
 with session(p) as k:
  b=k.get_board();fs=b.get_footprints();assert len(fs)==len({f.reference_field.text.value for f in fs}),'Duplicate references'
  fps={f.reference_field.text.value:{'xy':[f.position.x,f.position.y],'angle':f.orientation.degrees,'pads':sorted([(p.number,p.position.x,p.position.y,str(p.proto.pad_stack.drill),[(v.layer,v.size.x,v.size.y,v.shape) for v in p.padstack.copper_layers]) for p in f.definition.pads],key=lambda v:(v[0],v[1],v[2]))} for f in fs}
  copper={t.id.value:(t.net.name,t.layer,t.start.x,t.start.y,t.end.x,t.end.y,t.width) for t in b.get_tracks()}
  stack=b.get_stackup().proto.SerializeToString().hex()
  models={f.reference_field.text.value:[m.proto.SerializeToString().hex() for m in f.definition.models] for f in fs}
  return fps,copper,stack,models
base=Path(sys.argv[1]);a=capture(base);z=capture(D/'gpio_breakout.kicad_pcb')
checks={'stackup_unchanged':a[2]==z[2],'unique_27_references':len(z[0])==27}
for ref,f in a[0].items():
 if ref!='C1':checks['original_geometry_'+ref]=f==z[0][ref]
for ref in ['J1','J3']:checks['connector_model_'+ref]=a[3][ref]==z[3][ref]
changednets=DRIVEN|{'USB_D_P','USB_D_N','USB_VBUS_IN','GND'}
checked=[uid for uid,t in a[1].items() if t[0] not in changednets]
checks['all_unrelated_copper_preserved']=all(z[1].get(uid)==a[1][uid] for uid in checked)
checks['new_parts_exact']=set(z[0])-set(a[0])=={'U4','C3','C4','RN1','RN2','RN3','RN4','RN5','RN6'}
out={'passed':all(checks.values()),'checks':checks,'unrelated_tracks_checked':len(checked),'baseline_sha256':hashlib.sha256(base.read_bytes()).hexdigest(),'board_sha256':hashlib.sha256((D/'gpio_breakout.kicad_pcb').read_bytes()).hexdigest(),'original_C1_position_changed_for_startup_layout':True}
(D/'reports/qualification-fixes-preservation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));assert out['passed']
