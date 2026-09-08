"""Repair native IPC graphic-coordinate asymmetry, preserving pins, labels and IDs.

The initial translation helper incorrectly shifted local graphic definitions
alongside absolute pin coordinates. Register standard body centres in local
coordinates; leave every absolute pin and symbol ID intact.
"""
import json
from google.protobuf import descriptor_pool,message_factory
from update_addon_ipc import session,D,sheets,pins
from kipy.proto.common.types.enums_pb2 import KiCadObjectType

def vectors(msg):
 out=[]
 for f,v in msg.ListFields():
  if f.cpp_type!=f.CPPTYPE_MESSAGE:continue
  for c in (v if f.label==f.LABEL_REPEATED else [v]):
   if c.DESCRIPTOR.full_name=='kiapi.common.types.Vector2':out.append(c)
   else:out.extend(vectors(c))
 return out
with session(D/'gpio_breakout.kicad_sch') as k:
 root,ss=sheets(k);s=ss[0];out=[];allpins={}
 for f in s.get_symbols():
  ref=f.reference_field.text.value
  for p in pins(f).values():allpins[(p.position.x_nm,p.position.y_nm)]=p.orientation
  if ref not in ('J3','U1','U2','U3','R1','R2','C1','C2','F1','F2','JP4','JP5','#FLG1','#FLG2','#FLG3','#FLG4','#FLG5'):continue
  graphics=[]
  for item in f.definition.items:
   if not item.item.TypeName().endswith('SchematicGraphicShape'):continue
   m=message_factory.GetMessageClass(descriptor_pool.Default().FindMessageTypeByName(item.item.TypeName()))();item.item.Unpack(m);graphics.append((item,m))
  if not graphics:continue
  if ref=='J3':
   m=max((m for _,m in graphics if m.shape.HasField('rectangle')),key=lambda m:abs(m.shape.rectangle.top_left.x_nm-m.shape.rectangle.bottom_right.x_nm)*abs(m.shape.rectangle.top_left.y_nm-m.shape.rectangle.bottom_right.y_nm));ps=vectors(m);target_y=3810000
  else:ps=[p for _,m in graphics for p in vectors(m)];target_y=-1270000 if ref.startswith('#FLG') else 0
  cx=(min(p.x_nm for p in ps)+max(p.x_nm for p in ps))//2;cy=(min(p.y_nm for p in ps)+max(p.y_nm for p in ps))//2
  dx=-cx;dy=target_y-cy
  before={n:(p.position.x_nm,p.position.y_nm) for n,p in pins(f).items()}
  for item,m in graphics:
   for p in vectors(m):p.x_nm+=dx;p.y_nm+=dy
   item.item.Pack(m)
  s.update_items([f]);after=next(x for x in s.get_symbols() if x.id.value==f.id.value);assert before=={n:(p.position.x_nm,p.position.y_nm) for n,p in pins(after).items()}
  out.append({'ref':ref,'graphic_translation_nm':[dx,dy],'pins_and_symbol_uuid_preserved':True})
 for label in s.get_items([KiCadObjectType.KOT_SCH_GLOBAL_LABEL]):
  orient=allpins.get((label.position.x,label.position.y))
  # Pin orientation points toward the body; global-label tip points opposite.
  if orient==1:label.spin_style=3
  elif orient==2:label.spin_style=1
  else:continue
  s.update_items([label])
 s.save();root.save();(D/'reports/usb2-symbol-graphics-repair.json').write_text(json.dumps(out,indent=2)+'\n')
 print('Repaired graphic placement; all symbol/pin UUIDs and pin positions preserved.')
