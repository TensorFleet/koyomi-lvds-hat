"""Restore custom LCD footprints after native netlist import duplicated them."""
import json
from pathlib import Path
from update_addon_ipc import session,D
from usb2_interface import MAP
from kipy.board_types import Net
with session(Path('/private/tmp/gpio-usb-prior-native.kicad_pcb')) as k:
 source={f.reference_field.text.value:f for f in k.get_board().get_footprints()}
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();fps=b.get_footprints();out=[]
 for ref,original in source.items():
  matches=[f for f in fps if f.reference_field.text.value==ref]
  out.append({'ref':ref,'before':[(f.id.value,len(f.definition.pads),[f.position.x/1e6,f.position.y/1e6]) for f in matches],'original_pads':len(original.definition.pads)})
  b.remove_items(matches)
  if ref=='J1':
   for p in original.definition.pads:p.net=Net(name=MAP[ref].get(p.number) or '')
  b.create_items([original])
 b.refill_zones();b.save();(D/'reports/usb2-custom-footprint-restoration.json').write_text(json.dumps(out,indent=2)+'\n')
 print(out)
