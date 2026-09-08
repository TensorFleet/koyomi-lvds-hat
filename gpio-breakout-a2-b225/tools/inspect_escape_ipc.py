from update_addon_ipc import session,D
from native_astar import _layer_obstacles,_distance_to_segment
import math,json
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();out={}
 for layer in [3,5,34]:
  seg,circ,rect=_layer_obstacles(b,layer,'GPIO4',.2,.27)
  x,y=80.5,52.7
  out[layer]=dict(segments=[v for v in seg if _distance_to_segment(x,y,*v[:4])<v[4]],circles=[v for v in circ if math.dist((x,y),v[:2])<v[2]],rects=[v for v in rect if v[0]<x<v[2] and v[1]<y<v[3]])
 print(json.dumps(out,indent=2))
