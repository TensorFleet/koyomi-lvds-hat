"""Attach missing standard-library body models through native IPC."""
import shutil,json,hashlib
from pathlib import Path
from update_addon_ipc import session,D
from kipy.board_types import Footprint3DModel
from kipy.geometry import Vector3D
root=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels')
models={'U1':'Package_TO_SOT_SMD.3dshapes/SOT-363_SC-70-6.step','U2':'Package_TO_SOT_SMD.3dshapes/Texas_DRT-3.step','U3':'Package_TO_SOT_SMD.3dshapes/Texas_DRT-3.step','R1':'Resistor_SMD.3dshapes/R_0603_1608Metric.step','R2':'Resistor_SMD.3dshapes/R_0603_1608Metric.step','C1':'Capacitor_SMD.3dshapes/C_0603_1608Metric.step','C2':'Capacitor_SMD.3dshapes/C_0603_1608Metric.step'}
(D/'3dmodels/standard').mkdir(exist_ok=True);records=[]
for path in set(models.values()):
 target=D/'3dmodels/standard'/Path(path).name;shutil.copy2(root/path,target);records.append({'source_library':path,'local':str(target.relative_to(D)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'registration':'KiCad library default:offset0,rotation0,scale1','qualification':'Standard-library visualization; not manufacturer package metrology.'})
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board()
 for f in b.get_footprints():
  ref=f.reference_field.text.value
  if ref not in models:continue
  m=Footprint3DModel();m.filename='${KIPRJMOD}/3dmodels/standard/'+Path(models[ref]).name;m.scale=Vector3D.from_xyz(1,1,1);m.rotation=Vector3D.from_xyz(0,0,0);m.offset=Vector3D.from_xyz(0,0,0);m.visible=True;m.opacity=1
  f.definition.items=[x for x in f.definition.items if not isinstance(x,Footprint3DModel)]+[m];b.update_items([f])
 b.save()
(D/'reports/usb2-standard-models.json').write_text(json.dumps(records,indent=2)+'\n')
