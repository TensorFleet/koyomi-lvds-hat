"""Independent schematic XML versus native PCB-pad qualification."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
D=Path(__file__).resolve().parents[1];r=json.loads((D/'reports/qualification-native-snapshot.json').read_text());sch={}
for net in ET.parse(D/'reports/qualification-netlist.xml').findall('.//nets/net'):
 for node in net.findall('node'):sch[node.attrib['ref'],node.attrib['pin']]=net.attrib['name']
pcb={};pads={}
for ref,f in r['footprints'].items():
 for p in f['definition']['items']:
  if p['@type'].endswith('.Pad') and p.get('number'):pcb[ref,p['number']]=p.get('net',{}).get('name','');pads[ref,p['number']]=p
errors=[]
for key,net in pcb.items():
 sn=sch.get(key,'')
 if net and net!=sn:errors.append({'pad':key,'pcb':net,'schematic':sn})
 if not net and sn and not sn.startswith('unconnected-'):errors.append({'pad':key,'pcb':net,'schematic':sn})
ffc=['USB_VBUS']*4+['GND','USB_D_N','USB_D_P','GND','+5V_FFC','+5V_FFC','+3V3_FFC','GND','GPIO23','GPIO24','ID_SC','GPIO2','GPIO3','GND','ID_SD','GND']+[f'GPIO{i}' for i in range(4,10)]+['GND']+[f'GPIO{i}' for i in range(10,16)]+['GND']+[f'GPIO{i}' for i in range(16,22)]
for n,net in enumerate(ffc,1):
 if pcb.get(('J1',str(n)))!=net:errors.append({'ffc_pin':n,'expected':net,'actual':pcb.get(('J1',str(n)))})
j1=[p for p in r['footprints']['J1']['definition']['items'] if p['@type'].endswith('.Pad')];paste=sum('BL_F_Paste' in p['pad_stack']['layers'] for p in j1)
checks={'numbered_pad_netlist_parity':not errors,'forty_pin_contract':len(ffc)==40,'J1_paste_all_42_pads':paste==42,'USB_supply_separate_from_LCD':all(pcb['J1',str(n)]=='USB_VBUS' for n in range(1,5)) and pcb['J1','9']=='+5V_FFC' and pcb['J1','11']=='+3V3_FFC','independent_CC_pull_downs':pcb['J3','A5']==pcb['R1','1']=='USB_CC1' and pcb['J3','B5']==pcb['R2','1']=='USB_CC2' and pcb['R1','2']==pcb['R2','2']=='GND','PTC_then_reverse_blocker':pcb['J3','A4']==pcb['F2','1']=='USB_VBUS_RAW' and pcb['F2','2']==pcb['U1','1']=='USB_VBUS_IN' and pcb['U1','6']==pcb['J1','1']=='USB_VBUS'}
result={'passed':all(checks.values()),'checks':checks,'errors':errors,'numbered_board_pads_checked':len(pcb),'FFC_contacts':len(ffc),'J1_paste_pads':paste,'board_sha256':r['board_sha256'],'schematic_sha256':hashlib.sha256((D/'gpio_breakout.kicad_sch').read_bytes()).hexdigest(),'netlist_sha256':hashlib.sha256((D/'reports/qualification-netlist.xml').read_bytes()).hexdigest(),'FFC_pin_map':{str(n):net for n,net in enumerate(ffc,1)},'release_ready':False,'limits':'Connectivity proves topology, not dynamic reverse-blocking performance, inrush, host current allocation, cable mating or DPI timing.'}
(D/'reports/qualification-interface.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='FFC_pin_map'},indent=2))
if not result['passed']:raise SystemExit(2)
