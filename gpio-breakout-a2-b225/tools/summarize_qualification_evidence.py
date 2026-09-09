"""Bind final reports to source hashes; compare the C1 numbered native capture.

This emits review documentation, never fabrication files. It cannot substitute
for hardware measurements or clear the authoritative interconnect gate.
"""
import ast,csv,hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(n):return json.loads((D/'reports'/n).read_text())
bh=sha(D/'gpio_breakout.kicad_pcb');sh=sha(D/'gpio_breakout.kicad_sch')
interface=read('qualification-interface.json');assert interface['passed'] and interface['board_sha256']==bh and interface['schematic_sha256']==sh
preserve=read('qualification-fixes-preservation.json');assert preserve['passed'] and preserve['board_sha256']==bh
usb=read('usb2-path-audit.json');assert usb['board_sha256']==bh
assert read('dpi-qualification.json')['source_board_sha256']==bh
assert read('qualification-native-snapshot.json')['board_sha256']==bh
expected=['IO_VBUS_IN']*4+['GND','IO_USB_C_DN','IO_USB_C_DP','GND','LCD_+5V','LCD_+5V','LCD_+3V3','GND','LCD_SDA','LCD_SCL','LCD_ENABLE','LCD_VSYNC','LCD_HSYNC','GND','LCD_CLKIN','GND']+[f'LCD_B{i}' for i in range(6)]+['GND']+[f'LCD_G{i}' for i in range(6)]+['GND']+[f'LCD_R{i}' for i in range(6)]
c1=read('c1-paste-current.json');assert c1['paste_pads']==42 and c1['all_have_native_paste']
assert all(c1['pads'][str(i)]==net for i,net in enumerate(expected,1))
def findings(obj):
 if isinstance(obj,dict):
  if 'severity' in obj:yield obj
  for v in obj.values():yield from findings(v)
 elif isinstance(obj,list):
  for v in obj:yield from findings(v)
checks={}
for stem in ('drc','erc'):
 r=read(f'qualification-fixes-{stem}.json');vs=list(findings(r))
 errors=[v for v in vs if v['severity']=='error'];assert not errors
 checks[stem]={'errors':len(errors),'warnings':sum(v['severity']=='warning' for v in vs),'warning_types':sorted({v.get('type','') for v in vs})}
 if stem=='drc':assert not r.get('unconnected_items');checks[stem]['opens']=0
for p in (D/'tools').glob('*.py'):ast.parse(p.read_text(),filename=str(p))
# This CSV is the existing human-readable pin handoff, not a manufacturing BOM/CPL.
rows=read('interface-audit.json')['pin_map']
with (D/'interface-pinout.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
result={'desktop_checks_passed':True,'fabrication_released':False,'board_sha256':bh,'schematic_sha256':sh,'numbered_pads_checked':interface['numbered_board_pads_checked'],'FFC_functions_preserved':40,'C1_numbered_functions_match':40,'C1_paste_pads':42,'C1_source_sha256':c1['source_sha256'],'native_checks':checks,'models_reviewed':['renders/qualification-fixes-top.png','renders/qualification-fixes-right.png'],'model_limits':['J1 is a nominal envelope','J2 stacking socket is not selected'],'remaining':['Measure assembled USB channel in both Type-C orientations','Measure startup current, host droop and load voltage','Confirm Pi/panel timing and qualify source resistor population','Confirm installed catalog cable contact faces, length and latch/fold clearance'],'no_fabrication_generated':True}
(D/'reports/qualification-fixes-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
