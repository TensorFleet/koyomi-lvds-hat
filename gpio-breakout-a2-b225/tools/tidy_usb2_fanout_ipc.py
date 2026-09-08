from update_addon_ipc import session,D
from route_addon_ipc import copper
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();nets={n.name:n for n in b.get_nets()};remove=[]
 for t in b.get_tracks():
  a=(t.start.x/1e6,t.start.y/1e6);z=(t.end.x/1e6,t.end.y/1e6)
  if (t.net.name=='USB_CC2' and t.layer==3 and min(a[0],z[0])>=107 and max(a[1],z[1])<=60.8) or (t.net.name=='USB_VBUS_RAW' and t.layer==3 and min(a[0],z[0])>=107 and max(a[1],z[1])<=60.3):remove.append(t)
 b.remove_items(remove)
 copper(b,nets['USB_CC2'],[(107.13,60.75,3),(107.6,60.75,3),(108.15,60.35,3),(109.7,60.3,3)])
 copper(b,nets['USB_VBUS_RAW'],[(107.13,60.25,3),(107.55,60.25,3),(108.9,58.9,3),(109.5,58.9,3)])
 b.refill_zones();b.save()
 import json
 zones=[]
 for z in b.get_zones():
  for layer,polys in z.filled_polygons.items():
   if layer!=3:continue
   zones.append({'id':z.id.value,'mode':z.island_mode,'polys':[str(p.proto) for p in polys]})
 (D/'reports/usb2-ground-polygons.json').write_text(json.dumps(zones))
