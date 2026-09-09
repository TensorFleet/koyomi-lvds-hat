"""Add controlled USB startup and 22 Pi-side series provisions natively.

TPS22918 pin identity is from TI SLVSD76C, pin functions table. The load switch
precedes LM66100 so the latter retains reverse blocking. QOD is unconnected.
All array elements start at 0 ohms, pending the selected Pi/display timing test.
"""
import copy,json,uuid,sys
from pathlib import Path
from google.protobuf.json_format import ParseDict
from kipy.proto.schematic import schematic_types_pb2 as st
from kipy.schematic_types import SchematicSymbolInstance,GlobalLabel,NoConnectMarker
from kipy.geometry import Vector2
from update_addon_ipc import session,sheets,pins,shift,D
from qualification_design import ARRAYS,DRIVEN,EXTRA_MAP
array=ParseDict(json.loads((Path(sys.argv[1]) if len(sys.argv)>1 else D/'tools/assets/R_Pack04-native-template.json').read_text()),st.SchematicSymbolInstance())
with session(D/'gpio_breakout.kicad_sch') as k:
 root,ss=sheets(k);s=ss[0];old={f.reference_field.text.value:f for f in s.get_symbols()}
 assert not set(EXTRA_MAP)&old.keys(),'Additions already exist'
 creates=[]
 def clone(source,ref,xy,value,footprint=None):
  f=SchematicSymbolInstance(proto=copy.deepcopy(source));f.proto.id.value=str(uuid.uuid4());f.proto.path.CopyFrom(s.document.sheet_path)
  f.reference_field.text.value=ref;f.value_field.text.value=value
  if footprint:f.footprint_field.text.value=footprint
  local_graphics={i:copy.deepcopy(item) for i,item in enumerate(f.definition.items) if not item.item.TypeName().endswith('SchematicPin')}
  shift(f,*xy)
  for i,item in local_graphics.items():f.definition.items[i].CopyFrom(item)
  # Instance fields are kept legible above their symbol.
  for field,dy in [(f.reference_field,-12.7),(f.value_field,-10.16)]:field.text.position=Vector2.from_xy_mm(xy[0],xy[1]+dy)
  creates.append(f);return f
 for i,ref in enumerate(ARRAYS):clone(array,ref,(355.6+(i%3)*66.04,259.08+(i//3)*71.12),'0R x4 (DPI source option)','Resistor_SMD:R_Array_Convex_4x0603')
 u=clone(old['U1'].proto,'U4',(269.24,330.2),'TPS22918DBVR','Package_TO_SOT_SMD:SOT-23-6')
 u.proto.definition.id.library_nickname='GPIO_Qualification';u.proto.definition.id.entry_name='TPS22918DBV'
 u.definition.value_field.text.value='TPS22918DBV';u.definition.footprint_field.text.value='Package_TO_SOT_SMD:SOT-23-6'
 u.definition.datasheet_field.text.value='https://www.ti.com/lit/ds/symlink/tps22918.pdf'
 u.datasheet_field.text.value=u.definition.datasheet_field.text.value
 u.definition.description_field.text.value='TPS22918 adjustable slew load switch, TI SLVSD76C pin table'
 u.description_field.text.value=u.definition.description_field.text.value
 del u.proto.definition.footprint_filters[:];u.proto.definition.footprint_filters.append('SOT?23*')
 for child in u.proto.definition.items:
  if child.item.type_url.endswith('SchematicPin'):
   p=st.SchematicPin();child.item.Unpack(p);p.id.value=str(uuid.uuid4());p.visible=True
   p.name={'1':'VIN','2':'GND','3':'ON','4':'CT','5':'QOD','6':'VOUT'}[p.number]
   p.electrical_type=p.DESCRIPTOR.fields_by_name['electrical_type'].enum_type.values_by_name[{'1':'EPT_POWER_INPUT','2':'EPT_POWER_INPUT','3':'EPT_INPUT','4':'EPT_PASSIVE','5':'EPT_PASSIVE','6':'EPT_POWER_OUTPUT'}[p.number]].number
   if p.number=='4':p.position.x_nm=round(276.86e6);p.position.y_nm=round(330.2e6);p.orientation=p.DESCRIPTOR.fields_by_name['orientation'].enum_type.values_by_name['SPO_LEFT'].number
   child.item.Pack(p)
 clone(old['C1'].proto,'C3',(307.34,350.52),'10n 50V C0G 5%')
 clone(old['C1'].proto,'C4',(269.24,350.52),'1u 16V X7R')
 # Existing FFC labels retain their function names. Only Pi-side labels change.
 changes={}
 for n,p in pins(old['J2']).items():
  from update_addon_ipc import PI
  net=PI[int(n)]
  if net in DRIVEN:changes[(p.position.x_nm,p.position.y_nm)]=net+'_PI'
 p=pins(old['U1'])['1'];changes[(p.position.x_nm,p.position.y_nm)]='USB_VBUS_SOFT'
 labels=[]
 for l in s.get_labels():
  point=(l.position.x,l.position.y)
  if point in changes:l.text.value=changes[point];labels.append(l)
 assert len(labels)==23,len(labels)
 s.update_items(labels);s.create_items(creates)
 labels=[]
 for f in creates:
  for n,p in pins(f).items():
   net=EXTRA_MAP[f.reference_field.text.value][n]
   if net is None:l=NoConnectMarker();l.position=Vector2(p.position)
   else:
    l=GlobalLabel();l.text.value=net;l.position=Vector2(p.position);l.text.position=Vector2(p.position);l.text.attributes.size=Vector2.from_xy_mm(.9,.9)
   labels.append(l)
 s.create_items(labels);s.save();root.save()
 print('Added U4, C3/C4 and RN1–RN6 with native symbols and labels; PCB import pending.')
