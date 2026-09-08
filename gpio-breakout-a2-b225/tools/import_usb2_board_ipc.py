"""Native schematic-to-PCB import and USB component placement, preserving LCD copper."""
import json,os,shutil,subprocess
from pathlib import Path
from update_addon_ipc import session,D
from usb2_interface import MAP
from kipy.board_types import Footprint3DModel,Net
from kipy.geometry import Vector2,Vector3D,Angle

# Manufacturer component assets are already checked in. Optional refresh source
# must contain only the exact public Molex footprint and official STEP.
if os.environ.get('MOLEX_ASSET_DIR'):
 parts=Path(os.environ['MOLEX_ASSET_DIR'])
 shutil.copy2(parts/'USB_C_Receptacle_Molex_105450-0101.kicad_mod',D/'USB_A2.pretty/USB_C_Receptacle_Molex_105450-0101.kicad_mod')
 shutil.copy2(parts/'Molex_1054500101_official.stp',D/'3dmodels/Molex_1054500101_official.stp')
subprocess.run([os.environ['KICAD_SCH_CLI'],'sch','export','netlist','--format','kicadxml','--output',str(D/'reports/netlist.xml'),str(D/'gpio_breakout.kicad_sch')],check=True)
subprocess.run([os.environ['KICAD_SCH_CLI'],'sch','export','netlist','--format','kicadsexpr','--output',str(D/'reports/usb2-native.net'),str(D/'gpio_breakout.kicad_sch')],check=True)
POSITIONS={'J3':(109.045,61.5,90),'F2':(99.0,53.4,0),'U1':(95.9,53.4,0),
 'C1':(96.0,56.0,0),'C2':(93.8,56.0,0),'U2':(100.0,60.6,0),
 'U3':(100.5,65.5,0),'R1':(97.5,64.5,90),'R2':(97.5,67.3,90)}
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();before={x.id.value:x.proto.SerializeToString() for x in [*b.get_tracks(),*b.get_vias()]}
 r=b.import_netlist(str(D/'reports/usb2-native.net'),dry_run=True,delete_extra_footprints=False,update_footprints=False)
 (D/'reports/usb2-board-import-dry.txt').write_text(r.report)
 if r.error_count:raise RuntimeError(r.report)
 r=b.import_netlist(str(D/'reports/usb2-native.net'),dry_run=False,delete_extra_footprints=False,update_footprints=False)
 (D/'reports/usb2-board-import.txt').write_text(r.report)
 if r.error_count:raise RuntimeError(r.report)
 updates=[]
 for f in b.get_footprints():
  ref=f.reference_field.text.value
  if ref in POSITIONS:
   x,y,angle=POSITIONS[ref];f.orientation=Angle.from_degrees(angle);f.position=Vector2.from_xy_mm(x,y)
   if ref=='J3':
    m=Footprint3DModel();m.filename='${KIPRJMOD}/3dmodels/Molex_1054500101_official.stp'
    m.scale=Vector3D.from_xyz(1,1,1);m.rotation=Vector3D.from_xyz(0,0,180);m.offset=Vector3D.from_xyz(0,.195,1.63)
    m.visible=True;m.opacity=1;f.definition.items=[x for x in f.definition.items if not isinstance(x,Footprint3DModel)]+[m]
  if ref in MAP:
   for pad in f.definition.pads:pad.net=Net(name=MAP[ref].get(pad.number) or '')
   updates.append(f)
 b.update_items(updates)
 after={x.id.value:x.proto.SerializeToString() for x in [*b.get_tracks(),*b.get_vias()]}
 if before!=after:raise RuntimeError('PCB import altered existing tracks or vias')
 b.save()
 result={f.reference_field.text.value:dict(position=[f.position.x/1e6,f.position.y/1e6],rotation=f.orientation.degrees,
  pads={p.number:dict(net=p.net.name,xy=[p.position.x/1e6,p.position.y/1e6]) for p in f.definition.pads}) for f in b.get_footprints()}
 (D/'reports/usb2-placement.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Native USB PCB import saved; routing remains. Existing LCD copper unchanged.')
