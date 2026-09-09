"""Shorten reversible USB contact joins using native geometry; DRC is mandatory."""
import json,hashlib
from update_addon_ipc import session,D
from route_addon_ipc import copper
p=D/'gpio_breakout.kicad_pcb'
with session(p) as k:
 b=k.get_board();nets={n.name:n for n in b.get_nets()}
 remove=[t for t in b.get_tracks() if t.net.name in ('USB_D_P','USB_D_N') and (t.layer!=3 or min(t.start.x,t.end.x)>105.9e6)]
 remove += [v for v in b.get_vias() if v.net.name in ('USB_D_P','USB_D_N')]
 # Remove the former two via landing spurs without touching shared main routes.
 for t in b.get_tracks():
  if t.net.name in ('USB_D_P','USB_D_N') and t.layer==3 and abs(t.start.y-t.end.y)<10 and {round(t.start.x/1e6,3),round(t.end.x/1e6,3)}=={103.8,104.8}:remove.append(t)
 b.remove_items(remove)
 paths={
 'USB_D_P':[(107.13,61.25,3),(106.6725,61.25,3),(106.25,61.6725,3),(105.83,62,3)],
 'USB_D_N':[(107.13,61.75,3),(107.95,61.75,3),(107.95,61.75,5),(107.3,61,5),(104.8,61,5),(104.8,61,3)]}
 for n,path in paths.items():copper(b,nets[n],path,.20 if n=='USB_D_P' else .2)
 b.refill_zones();b.save()
 report={'board_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'removed_copper':[x.id.value for x in remove],'new_routes':paths,'status':'candidate_pending_native_drc_and_channel_review'}
 (D/'reports/usb2-short-joins.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Short USB contact joins saved; qualification pending.')
