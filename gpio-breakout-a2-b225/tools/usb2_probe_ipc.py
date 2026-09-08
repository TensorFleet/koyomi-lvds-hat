"""Native read-only baseline for GPIO A2 USB input addition."""
import json
from update_addon_ipc import session,sheets,pins,D
out={}
with session(D/'gpio_breakout.kicad_sch') as k:
 root,ss=sheets(k)
 out['symbols']={s.reference_field.text.value:{'position':[s.position.x/1e6,s.position.y/1e6],
  'value':s.value_field.text.value,'footprint':s.footprint_field.text.value,
  'pins':{n:dict(position=[p.position.x_nm/1e6,p.position.y_nm/1e6],name=p.name) for n,p in pins(s).items()}}
  for sheet in ss for s in sheet.get_symbols()}
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board()
 out['footprints']={f.reference_field.text.value:{'position':[f.position.x/1e6,f.position.y/1e6],
  'rotation':f.orientation.degrees,'value':f.value_field.text.value,
  'pads':{p.number:dict(net=p.net.name,xy=[p.position.x/1e6,p.position.y/1e6]) for p in f.definition.pads}}
  for f in b.get_footprints()}
 out['copper_counts']={'tracks':len(b.get_tracks()),'vias':len(b.get_vias())}
(D/'reports/usb2-baseline.json').write_text(json.dumps(out,indent=2)+'\n')
print('Native baseline saved; no board or schematic changes.')
