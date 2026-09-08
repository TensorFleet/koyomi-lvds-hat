import json
from update_addon_ipc import session,D
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();out={}
 for f in b.get_footprints():
  if f.reference_field.text.value not in ['J3','U1','U2','U3','C1','C2','F2','R1','R2']:continue
  out[f.reference_field.text.value]={'pads':[{'number':p.number,'net':p.net.name,'xy':[p.position.x/1e6,p.position.y/1e6],'angle':p.padstack.angle.degrees,'shape':[(s.size.x/1e6,s.size.y/1e6) for s in p.padstack.copper_layers]} for p in f.definition.pads]}
 (D/'reports/usb2-pad-geometry.json').write_text(json.dumps(out,indent=2)+'\n')
