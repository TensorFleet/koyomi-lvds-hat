from update_addon_ipc import session,D
from kipy.board_types import BoardText,BoardLayer
from kipy.geometry import Vector2
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();items=b.get_text()
 for t in items:
  if t.value.startswith('USB pins'):t.position=Vector2.from_xy_mm(81,78)
 b.update_items(items)
 for text,x,y in [('JP4 5V',58.8,58.2),('JP5 3V3',59,66),('F1 0.5A',59,62.6)]:
  t=BoardText();t.value=text;t.position=Vector2.from_xy_mm(x,y);t.layer=BoardLayer.BL_F_SilkS;t.attributes.size=Vector2.from_xy_mm(.8,.8);t.attributes.stroke_width=120000;b.create_items([t])
 b.save()
