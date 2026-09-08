"""Attach the inherited nominal envelope, explicitly not a supplier model."""
from update_addon_ipc import session,D
from kipy.board_types import Footprint3DModel
from kipy.geometry import Vector3D
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();f=next(f for f in b.get_footprints() if f.reference_field.text.value=='J1');assert len(f.definition.models)==0
 m=Footprint3DModel();m.filename='${KIPRJMOD}/3dmodels/ZF5S-40-01-nominal-envelope.wrl';m.scale=Vector3D.from_xyz(1,1,1);m.rotation=Vector3D.from_xyz(0,0,0);m.offset=Vector3D.from_xyz(0,0,0);m.visible=True;m.opacity=1;f.definition.items=list(f.definition.items)+[m];b.update_items([f]);b.save()
print('Attached labelled-in-documentation nominal envelope; mechanical approval remains blocked')
