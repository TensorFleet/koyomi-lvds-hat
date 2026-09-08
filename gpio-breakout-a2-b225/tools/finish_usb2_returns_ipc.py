import json
from update_addon_ipc import session,D
from route_addon_ipc import copper
from kipy.geometry import Vector2
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();nets={n.name:n for n in b.get_nets()};r=json.loads((D/'reports/drc.json').read_text());ids={i['uuid'] for x in r['violations'] if x['type']=='track_dangling' for i in x['items']}
 ids.update(x.id.value for x in b.get_vias() if x.net.name=='GND' and (abs(x.position.x/1e6-103.725)<.001 or (abs(x.position.x/1e6-101.9)<.001 and abs(x.position.y/1e6-65.2)<.001)))
 ids.update(x.id.value for x in b.get_tracks() if x.net.name=='GND' and (abs(x.start.x/1e6-102.825)<.001 or abs(x.start.x/1e6-101.9)<.001) and 65<=x.start.y/1e6<=66)
 old=json.loads((D/'reports/usb2-closure.json').read_text())[-1]['path']
 segments={tuple(sorted((tuple(a),tuple(z)))) for a,z in zip(old,old[1:]) if a[2]==z[2]}
 ids.update(t.id.value for t in b.get_tracks() if t.net.name=='USB_VBUS_RAW' and tuple(sorted(((round(t.start.x/1e6,6),round(t.start.y/1e6,6),t.layer),(round(t.end.x/1e6,6),round(t.end.y/1e6,6),t.layer)))) in segments)
 b.remove_items([x for x in [*b.get_tracks(),*b.get_vias()] if x.id.value in ids])
 copper(b,nets['GND'],[(102.825,66,3),(102.825,65.6,3),(101.9,65.6,3),(101.9,65.3,3),(101.9,65.3,4)])
 for f in b.get_footprints():
  ref=f.reference_field.text.value
  if ref not in ['U1','U2','U3','R1','R2','F2','C1','C2','J3']:continue
  f.reference_field.text.attributes.size=Vector2.from_xy_mm(.8,.8);f.reference_field.text.attributes.stroke_width=120000
  if ref=='U3':f.reference_field.text.position=Vector2.from_xy_mm(101.3,63.5)
  if ref=='R2':f.reference_field.text.position=Vector2.from_xy_mm(99.6,66.6)
  b.update_items([f])
 b.refill_zones();b.save()
