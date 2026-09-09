from update_addon_ipc import session,D
from kipy.geometry import Vector2,Angle
import json
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();key=lambda p:tuple(round(v,5) for v in p)
 rs=json.loads((D/'reports/startup-routing.json').read_text())
 gkeys={tuple(sorted((key(a),key(z)))) for r in rs if r['net']=='GND' for a,z in zip(r['path'],r['path'][1:]) if a[2]==z[2]}
 gvia={key(a[:2]) for r in rs if r['net']=='GND' for a,z in zip(r['path'],r['path'][1:]) if a[2]!=z[2]}
 remove=[]
 for t in b.get_tracks():
  ends=tuple(sorted((key((t.start.x/1e6,t.start.y/1e6,t.layer)),key((t.end.x/1e6,t.end.y/1e6,t.layer)))))
  if t.net.name in ('USB_VBUS_IN','USB_VBUS_SOFT','USB_SLEW_CT') or (t.net.name=='GND' and ends in gkeys):remove.append(t)
 for v in b.get_vias():
  if v.net.name in ('USB_VBUS_IN','USB_VBUS_SOFT','USB_SLEW_CT') or (v.net.name=='GND' and key((v.position.x/1e6,v.position.y/1e6)) in gvia):remove.append(v)
 b.remove_items(remove)
 for f in b.get_footprints():
  ref=f.reference_field.text.value
  if ref=='U4':f.orientation=Angle.from_degrees(90);f.position=Vector2.from_xy_mm(105.55,52.5);b.update_items([f])
  if ref=='C3':f.position=Vector2.from_xy_mm(105.55,55.35);b.update_items([f])
 b.save()
