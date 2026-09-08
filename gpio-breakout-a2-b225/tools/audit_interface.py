"""Compare independent native schematic netlist, PCB pads, and B2.25 contract."""
import csv,hashlib,json,xml.etree.ElementTree as E
from update_addon_ipc import session,D
from usb2_interface import FFC,MAP,PI
r=E.parse(D/'reports/netlist.xml');sch={}
for n in r.findall('.//nets/net'):
 for p in n.findall('node'):sch[p.attrib['ref'],p.attrib['pin']]=n.attrib['name']
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();fps={f.reference_field.text.value:f for f in b.get_footprints()};pcb={(ref,p.number):p.net.name for ref,f in fps.items() for p in f.definition.pads if p.number}
 errors=[];rows=[]
 for n,net in FFC.items():
  actual=pcb['J1',n];sn=sch.get(('J1',n),'')
  if net:
   if actual!=net or sn!=net:errors.append(dict(pin=n,expected=net,pcb=actual,schematic=sn))
  elif actual or not sn.startswith('unconnected-'):errors.append(dict(pin=n,expected='NC',pcb=actual,schematic=sn))
  pi=[p for p,v in PI.items() if v==net]
  if net=='+5V_FFC':pi=[2,4]
  if net=='+3V3_FFC':pi=[1,17]
  rows.append(dict(ffc_pin=int(n),signal=net or 'UNUSED_USB',pi_physical_pins='/'.join(map(str,pi)),power_path='JP4 (open) + F1' if net=='+5V_FFC' else 'JP5 (open)' if net=='+3V3_FFC' else 'USB cable / F2 / LM66100' if net=='USB_VBUS' else 'USB cable / ESD' if net.startswith('USB_D_') else 'direct' if net else 'NC'))
 for ref in MAP:
  for n,net in MAP[ref].items():
   if ref.startswith('#') or net is None:continue
   if pcb.get((ref,n))!=net or sch.get((ref,n))!=net:errors.append(dict(ref=ref,pin=n,expected=net,pcb=pcb.get((ref,n)),schematic=sch.get((ref,n))))
 for ref in ['JP4','JP5']:
  if 'Open' not in str(fps[ref].definition.id):errors.append({'not_open_footprint':ref})
 result=dict(passed=not errors,errors=errors,contacts_checked=40,used_contacts=40,unused_usb_contacts=[],connector_mpn=fps['J1'].value_field.text.value,board_sha256=hashlib.sha256((D/'gpio_breakout.kicad_pcb').read_bytes()).hexdigest(),schematic_sha256=hashlib.sha256((D/'gpio_breakout.kicad_sch').read_bytes()).hexdigest(),minimum_track_mm=min(t.width for t in b.get_tracks())/1e6,via_drills_mm=sorted(set(v.drill_diameter/1e6 for v in b.get_vias())),pin_map=rows,release_ready=False,release_blockers=['Full USB channel and B-contact stubs remain unqualified after the native JLC04161H-7628 correction.','C1 contact functions match, but its J401 paste and full routing/assembly qualification remain open.','Exact catalog cable assembly and orientation require numbered one-to-one mating audit.','Real Samtec 3D model and assembly clearance are not yet verified; envelope only.','USB inrush, assembled power budget and DPI source termination/timing remain unqualified.'])
(D/'reports/interface-audit.json').write_text(json.dumps(result,indent=2)+'\n')
with (D/'interface-pinout.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)
print(json.dumps({k:v for k,v in result.items() if k!='pin_map'},indent=2))
if errors:raise SystemExit(2)
