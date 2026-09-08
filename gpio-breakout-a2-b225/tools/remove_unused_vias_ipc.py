"""Remove only native-DRC dangling vias after successful surface closures."""
import json
from update_addon_ipc import session,D
r=json.loads((D/'reports/drc.json').read_text());ids={v['items'][0]['uuid'] for v in r['violations'] if v['type']=='via_dangling'}
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();vias=[v for v in b.get_vias() if v.id.value in ids];assert len(vias)==len(ids);b.remove_items(vias);b.refill_zones();b.save()
print('Removed',len(ids),'unused vias')
