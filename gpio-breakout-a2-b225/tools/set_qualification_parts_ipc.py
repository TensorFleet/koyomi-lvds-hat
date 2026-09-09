"""Bind new symbols to their actual component choices, not donor resistor values."""
from update_addon_ipc import session,sheets,D
from kipy.schematic_types import SchematicField
from kipy.board_types import Field
from kipy.geometry import Vector2
PARTS={'U4':('C131941','TPS22918DBVR'),'C3':('C76599','C1608C0G1H103JT000N')}
PARTS.update({f'RN{i}':('C1952','4D03WGJ0000T5E') for i in range(1,7)})
with session(D/'gpio_breakout.kicad_sch') as k:
 root,ss=sheets(k)
 for s in ss:
  updates=[]
  for f in s.get_symbols():
   ref=f.reference_field.text.value
   if ref not in PARTS:continue
   fields=[x for x in f.user_fields if x.name not in ('LCSC','MPN')]
   for name,text in zip(('LCSC','MPN'),PARTS[ref]):
    x=SchematicField();x.name=name;x.text.value=text;x.visible=False;x.text.position=f.position;fields.append(x)
   f.user_fields=fields;updates.append(f)
  s.update_items(updates);s.save()
 root.save()
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board()
 for f in b.get_footprints():
  ref=f.reference_field.text.value
  if ref not in PARTS:continue
  items=[x for x in f.definition.items if not isinstance(x,Field) or x.name not in ('LCSC','MPN')]
  for name,text in zip(('LCSC','MPN'),PARTS[ref]):
   x=Field();x.name=name;x.text.value=text;x.visible=False;x.text.position=f.position;items.append(x)
  f.definition.items=items;b.update_items([f])
 b.save()
print('New component identities set in both editable sources; no BOM generated.')
