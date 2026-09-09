"""Make qualification circuits legible without changing electrical pin identity.

IPC pin positions are absolute, whereas symbol graphics use local coordinates.
Only symbols, pins, fields and attached labels move when arranging the page.
"""
import json
from google.protobuf import descriptor_pool,message_factory
from google.protobuf.json_format import MessageToDict
from kipy.proto.schematic import schematic_types_pb2 as st
from kipy.proto.common.types.enums_pb2 import KiCadObjectType
from kipy.geometry import Vector2
from update_addon_ipc import session,D,sheets,pins,shift

def vectors(msg):
 out=[]
 for f,v in msg.ListFields():
  if f.cpp_type!=f.CPPTYPE_MESSAGE:continue
  for c in (v if f.label==f.LABEL_REPEATED else [v]):
   if c.DESCRIPTOR.full_name=='kiapi.common.types.Vector2':out.append(c)
   else:out.extend(vectors(c))
 return out
with session(D/'gpio_breakout.kicad_sch') as k:
 root,ss=sheets(k);s=ss[0];moves={};results=[]
 for f in s.get_symbols():
  ref=f.reference_field.text.value
  if ref not in ['U4','C3','C4']+[f'RN{i}' for i in range(1,7)]:continue
  before={n:(p.position.x_nm,p.position.y_nm) for n,p in pins(f).items()}
  if ref.startswith('RN'):
   i=int(ref[2:])-1;xy=(355.6+(i%3)*66.04,259.08+(i//3)*71.12)
   # shift currently moves graphics too; normalize them below afterwards.
   shift(f,*xy)
   for field,dy in [(f.reference_field,-3.81),(f.value_field,0)]:
    field.text.position=Vector2.from_xy_mm(xy[0]+18,xy[1]+dy)
    field.text.attributes.size=Vector2.from_xy_mm(.9,.9)
  graphics=[]
  for item in f.definition.items:
   if not item.item.TypeName().endswith('SchematicGraphicShape'):continue
   m=message_factory.GetMessageClass(descriptor_pool.Default().FindMessageTypeByName(item.item.TypeName()))();item.item.Unpack(m);graphics.append((item,m))
  ps=[p for _,m in graphics for p in vectors(m)]
  cx=(min(p.x_nm for p in ps)+max(p.x_nm for p in ps))//2;cy=(min(p.y_nm for p in ps)+max(p.y_nm for p in ps))//2
  for item,m in graphics:
   for p in vectors(m):p.x_nm-=cx;p.y_nm-=cy
   item.item.Pack(m)
  for n,p in pins(f).items():moves[before[n]]=(p.position.x_nm,p.position.y_nm)
  s.update_items([f]);results.append({'reference':ref,'graphics_centered_locally':True,'position_mm':[f.position.x/1e6,f.position.y/1e6]})
 # Keep passive fields beside their bodies, clear of vertical net labels.
 for f in s.get_symbols():
  ref=f.reference_field.text.value
  if ref in ('C1','C2','C3','C4','F1','F2'):
   for field,dy in [(f.reference_field,-1.27),(f.value_field,1.27)]:
    field.text.position=Vector2.from_xy_mm(f.position.x/1e6+5.08,f.position.y/1e6+dy)
    field.text.attributes.angle=0
   s.update_items([f])
 orientations={}
 for f in s.get_symbols():
  for p in pins(f).values():orientations[(p.position.x_nm,p.position.y_nm)]=p.orientation
 items=s.get_items([KiCadObjectType.KOT_SCH_GLOBAL_LABEL,KiCadObjectType.KOT_SCH_NO_CONNECT])
 for item in items:
  xy=(item.position.x,item.position.y)
  if xy in moves:item.position=Vector2.from_xy_mm(moves[xy][0]/1e6,moves[xy][1]/1e6)
  if hasattr(item,'spin_style'):
   orient=orientations.get((item.position.x,item.position.y))
   spins={st.SPO_RIGHT:st.SLSS_LEFT,st.SPO_LEFT:st.SLSS_RIGHT,st.SPO_UP:st.SLSS_BOTTOM,st.SPO_DOWN:st.SLSS_UP}
   if orient in spins:
    item.spin_style=spins[orient]
    # Native deserialization applies EDA_TEXT after spin_style. Supply both.
    item.text.position=item.position
    item.text.attributes.angle=90 if orient in (st.SPO_UP,st.SPO_DOWN) else 0
    attrs=item.proto.text.attributes
    attrs.horizontal_alignment=attrs.DESCRIPTOR.fields_by_name['horizontal_alignment'].enum_type.values_by_name['HA_RIGHT' if orient in (st.SPO_RIGHT,st.SPO_UP) else 'HA_LEFT'].number
  s.update_items([item])
 s.save();root.save()
 arr=next(f for f in s.get_symbols() if f.reference_field.text.value=='RN1')
 (D/'tools/assets/R_Pack04-native-template.json').write_text(json.dumps(MessageToDict(arr.proto),indent=2)+'\n')
 (D/'reports/qualification-schematic-layout.json').write_text(json.dumps(results,indent=2)+'\n')
 print('Placed all new circuits inside the page and normalized local symbol graphics.')
