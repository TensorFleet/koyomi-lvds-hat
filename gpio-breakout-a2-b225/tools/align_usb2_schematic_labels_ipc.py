"""Point horizontal net labels away from symbol bodies without moving anchors."""
from update_addon_ipc import session,D,sheets,pins
from kipy.proto.common.types.enums_pb2 import KiCadObjectType
with session(D/'gpio_breakout.kicad_sch') as k:
 root,ss=sheets(k);s=ss[0];lookup={}
 for f in s.get_symbols():
  for p in pins(f).values():lookup[p.position.x_nm,p.position.y_nm]=p.orientation
 for l in s.get_items([KiCadObjectType.KOT_SCH_GLOBAL_LABEL]):
  orientation=lookup.get((l.position.x,l.position.y))
  if orientation not in (1,2):continue
  l.spin_style=1 if orientation==1 else 3;l.text.attributes.angle=180 if orientation==1 else 0;s.update_items([l])
 s.save();root.save()
