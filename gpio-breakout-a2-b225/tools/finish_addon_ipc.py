"""Native source cleanup and independently audited numbered LCD interface."""
import hashlib,json,xml.etree.ElementTree as E
from update_addon_ipc import session,sheets,pins,shift,D,FFC,MAP
from kipy.schematic_types import GlobalLabel,NoConnectMarker
from kipy.geometry import Vector2
from kipy.board_types import BoardLayer
from kipy.proto.common.types.enums_pb2 import KiCadObjectType

def main():
 with session(D/'gpio_breakout.kicad_sch') as k:
  root,ss=sheets(k);s=ss[0];f=next(f for f in s.get_symbols() if f.reference_field.text.value=='J1');anchors={(p.position.x_nm,p.position.y_nm) for p in pins(f).values()}
  old=[l for l in s.get_labels() if (l.position.x,l.position.y) in anchors]
  old += [v for v in s.get_items(types=[KiCadObjectType.KOT_SCH_NO_CONNECT]) if isinstance(v,NoConnectMarker) and (v.position.x,v.position.y) in anchors]
  s.remove_items(old);shift(f,69.85,80.01);s.update_items([f]);items=[]
  for n,p in pins(f).items():
   net=FFC[n]
   if net is None:l=NoConnectMarker();l.position=Vector2(p.position)
   else:
    l=GlobalLabel();l.text.value=net;l.position=Vector2(p.position);l.text.position=l.position;l.text.attributes.size=Vector2.from_xy_mm(.9,.9)
   items.append(l)
  s.create_items(items);s.save();root.save()
 with session(D/'gpio_breakout.kicad_pcb') as k:
  b=k.get_board();updates=[]
  for f in b.get_footprints():
   f.reference_field.visible=False;f.value_field.visible=False;updates.append(f)
  b.update_items(updates)
  texts=b.get_text()
  for t in texts:
   if t.layer==BoardLayer.BL_B_SilkS:t.attributes.mirrored=True
  b.update_items(texts);b.save()
 print('Native schematic grid and silk cleanup saved')
if __name__=='__main__':main()
