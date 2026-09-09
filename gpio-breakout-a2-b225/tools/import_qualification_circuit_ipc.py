"""Import native schematic additions, keep existing USB routes and power geometry."""
import json,os,subprocess
from update_addon_ipc import session,D
from qualification_design import POSITIONS,DRIVEN
from kipy.geometry import Vector2,Angle
cli=os.environ['KICAD_CLI']
for fmt,name in [('kicadxml','qualification-updated-netlist.xml'),('kicadsexpr','qualification-updated.net')]:
 subprocess.run([cli,'sch','export','netlist','--format',fmt,'--output',str(D/'reports'/name),str(D/'gpio_breakout.kicad_sch')],check=True)
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board()
 # Original driven nets will be routed through source-side arrays, with the
 # original FFC function names retained downstream. Remove their old copper.
 remove=[x for x in [*b.get_tracks(),*b.get_vias()] if x.net.name in DRIVEN or x.net.name=='USB_VBUS_IN']
 # Moving C1 also requires its short GND connection to be rebuilt.
 remove.extend(t for t in b.get_tracks() if t.net.name=='GND' and any(abs(p.x/1e6-99.775)<.001 and abs(p.y/1e6-56)<.001 for p in (t.start,t.end)))
 b.remove_items(remove)
 r=b.import_netlist(str(D/'reports/qualification-updated.net'),dry_run=False,delete_extra_footprints=False,update_footprints=False)
 (D/'reports/qualification-board-import.txt').write_text(r.report)
 assert r.error_count==0,r.report
 updates=[]
 for f in b.get_footprints():
  ref=f.reference_field.text.value
  if ref in POSITIONS:
   x,y,rot=POSITIONS[ref];f.orientation=Angle.from_degrees(rot);f.position=Vector2.from_xy_mm(x,y)
   f.reference_field.text.position=Vector2.from_xy_mm(x,y-2.8)
   f.reference_field.text.attributes.size=Vector2.from_xy_mm(.7,.7)
   f.value_field.visible=False;updates.append(f)
 b.update_items(updates);b.save()
 (D/'reports/qualification-placement.json').write_text(json.dumps({f.reference_field.text.value:{'xy':[f.position.x/1e6,f.position.y/1e6],'pads':{p.number:{'xy':[p.position.x/1e6,p.position.y/1e6],'net':p.net.name} for p in f.definition.pads}} for f in b.get_footprints()},indent=2)+'\n')
 print('Imported additions; removed',len(remove),'old copper items for the changed circuits. Routing remains.')
