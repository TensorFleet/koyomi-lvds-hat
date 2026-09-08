"""Arrange GUI-imported official library symbols and connect USB2 using native IPC."""
import copy,json,uuid
from update_addon_ipc import session,sheets,pins,shift,D
from usb2_interface import MAP,FOOTPRINTS,VALUES
from kipy.schematic_types import SchematicSymbolInstance,GlobalLabel,NoConnectMarker
from kipy.proto.common.types.enums_pb2 import KiCadObjectType
from kipy.geometry import Vector2

PLACEMENTS={'J3':(60.96,260.35),'U2':(130.81,251.46),'U3':(130.81,290.83),
 'R1':(165.10,281.94),'R2':(185.42,281.94),'F2':(130.81,330.20),
 'U1':(180.34,330.20),'C1':(154.94,350.52),'C2':(215.90,350.52),
 '#FLG4':(109.22,350.52),'#FLG5':(130.81,350.52)}

with session(D/'gpio_breakout.kicad_sch') as k:
 root,ss=sheets(k);s=ss[0];old={f.reference_field.text.value:f for f in s.get_symbols()}
 assert old['J3'].value_field.text.value=='USB_C_Receptacle','Expected GUI-imported standard USB connector'
 assert old['U1'].value_field.text.value=='LM66100DCK'
 assert old['U2'].value_field.text.value=='TPD2EUSB30'
 templates={'U3':'U2','R2':'R1','C2':'C1','F2':'F1','#FLG4':'#FLG2','#FLG5':'#FLG2'}
 creates=[]
 for ref,source in templates.items():
  assert ref not in old
  f=SchematicSymbolInstance(proto=copy.deepcopy(old[source].proto));f.proto.id.value=str(uuid.uuid4())
  f.proto.path.CopyFrom(s.document.sheet_path);f.reference_field.text.value=ref
  creates.append(f);old[ref]=f
 updates=[]
 for ref,position in PLACEMENTS.items():
  f=old[ref];shift(f,*position)
  if ref in VALUES:f.value_field.text.value=VALUES[ref];f.footprint_field.text.value=FOOTPRINTS[ref]
  if ref not in templates:updates.append(f)
 s.update_items(updates);s.create_items(creates)
 j1=next(f for f in s.get_symbols() if f.reference_field.text.value=='J1')
 changed_pins={n:p for n,p in pins(j1).items() if n in ('1','2','3','4','6','7')}
 points={(p.position.x_nm,p.position.y_nm) for p in changed_pins.values()}
 markers=s.get_items([KiCadObjectType.KOT_SCH_NO_CONNECT])
 s.remove_items([m for m in markers if (m.position.x,m.position.y) in points])
 labels=[];seen=set()
 for f in s.get_symbols():
  ref=f.reference_field.text.value
  if ref not in PLACEMENTS and ref!='J1':continue
  for n,pin in pins(f).items():
   if ref=='J1' and n not in changed_pins:continue
   net=MAP[ref].get(n)
   key=(pin.position.x_nm,pin.position.y_nm,net)
   if key in seen:continue
   seen.add(key)
   if net is None:l=NoConnectMarker();l.position=Vector2(pin.position)
   else:
    l=GlobalLabel();l.text.value=net;l.position=Vector2(pin.position);l.text.position=Vector2(pin.position)
    l.text.attributes.size=Vector2.from_xy_mm(.9,.9)
   labels.append(l)
 s.create_items(labels);s.save();root.save()
 out={f.reference_field.text.value:dict(uuid=f.id.value,path=[x.value for x in s.document.sheet_path.path],
   value=f.value_field.text.value,footprint=f.footprint_field.text.value,pins=list(pins(f))) for f in s.get_symbols()}
 (D/'reports/usb2-symbols.json').write_text(json.dumps(out,indent=2)+'\n')
 print('USB2 schematic native source updated; PCB import and audits remain.')
