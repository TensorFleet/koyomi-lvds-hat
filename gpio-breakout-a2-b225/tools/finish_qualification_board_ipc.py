"""Connect the isolated ground pour and finish labels/standard package models."""
from update_addon_ipc import session,D
from kipy.board_types import Footprint3DModel
from kipy.geometry import Vector2,Vector3D
from route_addon_ipc import copper
from pathlib import Path
import shutil,json
M=Path('/Users/hyper/projects/tensorfleet/vaio_p_modding/tools/kicad11-nightly-20260905/KiCad/KiCad.app/Contents/SharedSupport/3dmodels')
models={'U4':'Package_TO_SOT_SMD.3dshapes/SOT-23-6.step','C3':'Capacitor_SMD.3dshapes/C_0603_1608Metric.step','C4':'Capacitor_SMD.3dshapes/C_0603_1608Metric.step','F1':'Fuse.3dshapes/Fuse_1206_3216Metric.step','F2':'Fuse.3dshapes/Fuse_1206_3216Metric.step'}
models.update({f'RN{i}':'Resistor_SMD.3dshapes/R_Array_Convex_4x0603.step' for i in range(1,7)})
for rel in set(models.values()):
 dest=D/'3dmodels/qualification'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(M/rel,dest)
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();nets={n.name:n for n in b.get_nets()}
 copper(b,nets['GND'],[(99.6,66.1,3),(99.6,66.1,4)])
 labels={'U4':(108,55.2),'C1':(99.5,54.2),'C3':(98.5,57),'C4':(100,59.4)}
 for f in b.get_footprints():
  ref=f.reference_field.text.value
  if ref in models:
   m=Footprint3DModel();m.filename='${KIPRJMOD}/3dmodels/qualification/'+models[ref];m.scale=Vector3D.from_xyz(1,1,1);m.visible=True;m.opacity=1
   f.definition.items=[x for x in f.definition.items if not isinstance(x,Footprint3DModel)]+[m]
  if ref in labels:f.reference_field.text.position=Vector2.from_xy_mm(*labels[ref]);f.reference_field.text.attributes.angle=0
  if ref in labels or ref.startswith('RN'):
   f.reference_field.text.attributes.size=Vector2.from_xy_mm(.8,.8);f.reference_field.text.attributes.stroke_width=120000
  b.update_items([f])
 b.refill_zones();b.save();print('Ground stitch, readable labels and standard package models saved.')
