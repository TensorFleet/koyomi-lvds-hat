"""Native KiCad migration from immutable GPIO A1 to LCD-only B2.25 A2."""
import copy,json,os,subprocess,tempfile,time,uuid
from pathlib import Path
from contextlib import contextmanager
from kipy import KiCad
from kipy.schematic import Schematic
from kipy.proto.common.types import DocumentType
from kipy.proto.schematic import schematic_types_pb2
from kipy.schematic_types import GlobalLabel,NoConnectMarker,SchematicSymbolInstance
from kipy.board_types import FootprintInstance,Net,BoardText,BoardLayer
from kipy.geometry import Vector2,Angle
from google.protobuf import descriptor_pool,message_factory
D=Path(__file__).resolve().parents[1]
CLI=os.environ.get('KICAD_CLI','/Users/hyper/projects/tensorfleet/vaio_p_modding/tools/kicad11-b2231-parity/KiCad.app/Contents/MacOS/kicad-cli')
CARRIER=Path(os.environ.get('B225_SOURCE','/private/tmp/carrier-b225-usbc-outward/kicad-b2.25-a2-combined-io'))
@contextmanager
def session(path):
 with tempfile.TemporaryDirectory(prefix='ga-',dir='/private/tmp') as temp:
  sock=Path(temp)/'a.sock'
  with tempfile.TemporaryFile(mode='w+t') as log:
   cli=os.environ.get('KICAD_SCH_CLI',CLI) if str(path).endswith('.kicad_sch') else CLI
   proc=subprocess.Popen([cli,'api-server','--socket',str(sock),str(path)],stdout=log,stderr=log)
   try:
    end=time.monotonic()+60
    while not sock.exists():
     if proc.poll() is not None or time.monotonic()>end:log.seek(0);raise RuntimeError(log.read() or 'IPC timeout')
     time.sleep(.1)
    k=KiCad(socket_path='ipc://'+str(sock),timeout_ms=10000)
    for i in range(100):
     try:k.ping();break
     except Exception:time.sleep(.1)
    yield k
   finally:proc.terminate();proc.wait(timeout=10)
def sheets(k):
 root=Schematic(k._client,k.get_open_documents(DocumentType.DOCTYPE_SCHEMATIC)[0]);out=[]
 def visit(inst):
  doc=copy.deepcopy(root.document);doc.sheet_path.CopyFrom(inst.path.proto);out.append(Schematic(root.client,doc))
  for c in inst.children:visit(c)
 for inst in root.get_hierarchy():visit(inst)
 return root,out

def pins(sym):
 out={}
 for child in sym.proto.definition.items:
  if child.item.type_url.endswith('SchematicPin'):
   p=schematic_types_pb2.SchematicPin();child.item.Unpack(p);out[p.number]=p
 return out

def shift(sym,x,y):
 dx=round(x*1e6)-sym.position.x;dy=round(y*1e6)-sym.position.y;sym.position=Vector2.from_xy_mm(x,y)
 def translate(msg):
  for field,value in msg.ListFields():
   if field.cpp_type!=field.CPPTYPE_MESSAGE:continue
   for child in (value if field.label==field.LABEL_REPEATED else [value]):
    if child.DESCRIPTOR.full_name=='kiapi.common.types.Vector2':child.x_nm+=dx;child.y_nm+=dy
    else:translate(child)
 for name in ['reference_field','value_field','footprint_field','datasheet_field','description_field']:
  f=getattr(sym,name);v=f.text.position;v.x+=dx;v.y+=dy;f.text.position=v
 for child in sym.definition.items:
  msg=message_factory.GetMessageClass(descriptor_pool.Default().FindMessageTypeByName(child.item.TypeName()))();child.item.Unpack(msg);translate(msg);child.item.Pack(msg)

PI={1:'+3V3',2:'+5V',3:'GPIO2',4:'+5V',5:'GPIO3',6:'GND',7:'GPIO4',8:'GPIO14',9:'GND',10:'GPIO15',11:'GPIO17',12:'GPIO18',13:'GPIO27',14:'GND',15:'GPIO22',16:'GPIO23',17:'+3V3',18:'GPIO24',19:'GPIO10',20:'GND',21:'GPIO9',22:'GPIO25',23:'GPIO11',24:'GPIO8',25:'GND',26:'GPIO7',27:'ID_SD',28:'ID_SC',29:'GPIO5',30:'GND',31:'GPIO6',32:'GPIO12',33:'GPIO13',34:'GND',35:'GPIO19',36:'GPIO16',37:'GPIO26',38:'GPIO20',39:'GND',40:'GPIO21'}
aliases={'CS_GPIO24':'GPIO24','BL_GPIO18':'GPIO18','MISO_GPIO19':'GPIO19','MOSI_GPIO20':'GPIO20','SCLK_GPIO21':'GPIO21','+5V':'+5V_FFC','+3V3_PI':'+3V3_FFC'}
source=json.loads((D/'reports/carrier-interface-source.json').read_text())
FFC={str(v['pin']):None if v['pin'] in [1,2,3,4,6,7] else aliases.get(v['carrier'],v['carrier']) for v in source['pin_map']}
MAP={'J1':FFC,'J2':{str(n):v for n,v in PI.items()},'F1':{'1':'+5V_LNK','2':'+5V_FFC'},'JP4':{'1':'+5V','2':'+5V_LNK'},'JP5':{'1':'+3V3','2':'+3V3_FFC'},'TP4':{'1':'GND'},'TP5':{'1':'+3V3'},'#FLG1':{'1':'+3V3'},'#FLG2':{'1':'+5V'},'#FLG3':{'1':'GND'}}
REMOVE={'JP1','JP2','JP3','TP1','TP2','TP3'}

def main():
 with session(CARRIER/'vaio_cm5_carrier.kicad_sch') as k:
  _,ss=sheets(k);donor=next(s for sh in ss for s in sh.get_symbols() if s.reference_field.text.value=='JPERIPH1');donor=SchematicSymbolInstance(proto=copy.deepcopy(donor.proto))
 with session(D/'gpio_breakout.kicad_sch') as k:
  root,ss=sheets(k);s=ss[0];old={f.reference_field.text.value:f for f in s.get_symbols()}
  assert old['J1'].value_field.text.value.startswith('FH41')
  opened=copy.deepcopy(old['JP1'].proto)
  s.remove_items(list(s.get_labels())+[old[r] for r in REMOVE|{'J1','JP4','JP5'}])
  donor.proto.id.value=str(uuid.uuid4());donor.proto.path.CopyFrom(s.document.sheet_path);donor.reference_field.text.value='J1';shift(donor,70*1.0,80*1.0)
  creates=[donor]
  for ref in ['JP4','JP5']:
   f=SchematicSymbolInstance(proto=copy.deepcopy(opened));f.proto.id.value=str(uuid.uuid4());f.proto.path.CopyFrom(s.document.sheet_path);f.reference_field.text.value=ref;f.value_field.text.value='5V LINK OPEN' if ref=='JP4' else '3V3 LINK OPEN';shift(f,old[ref].position.x/1e6,old[ref].position.y/1e6);creates.append(f)
  s.create_items(creates)
  labels=[]
  for f in s.get_symbols():
   ref=f.reference_field.text.value
   if ref not in MAP:continue
   for n,p in pins(f).items():
    value=MAP[ref].get(n)
    if value is None:l=NoConnectMarker();l.position=Vector2(p.position)
    else:
     l=GlobalLabel();l.text.value=value;l.position=Vector2(p.position);l.text.position=Vector2(p.position);l.text.attributes.size=Vector2.from_xy_mm(.9,.9)
    labels.append(l)
  s.create_items(labels)
  s.save();root.save()
  capture={f.reference_field.text.value:dict(uuid=f.id.value,path=[x.value for x in s.document.sheet_path.path]) for f in s.get_symbols()}
 with session(CARRIER/'vaio_cm5_carrier.kicad_pcb') as k:
  donor=FootprintInstance(proto=copy.deepcopy(next(f for f in k.get_board().get_footprints() if f.reference_field.text.value=='JPERIPH1').proto))
 with session(D/'gpio_breakout.kicad_pcb') as k:
  b=k.get_board();old={f.reference_field.text.value:f for f in b.get_footprints()};openfp=copy.deepcopy(old['JP1'].proto)
  b.remove_items(list(b.get_tracks())+list(b.get_vias())+[old[r] for r in REMOVE|{'J1','JP4','JP5'}])
  donor.proto.id.value=str(uuid.uuid4());donor.reference_field.text.value='J1';donor.orientation=Angle.from_degrees(180);donor.position=Vector2.from_xy_mm(81,55.23)
  creates=[donor]
  for ref in ['JP4','JP5']:
   f=FootprintInstance(proto=copy.deepcopy(openfp));f.proto.id.value=str(uuid.uuid4());f.reference_field.text.value=ref;f.orientation=old[ref].orientation;f.position=old[ref].position;f.value_field.text.value=ref+' OPEN';creates.append(f)
  for f in creates:
   ref=f.reference_field.text.value
   for p in f.definition.pads:p.net=Net(name=MAP[ref].get(p.number) or '')
   del f.proto.symbol_path.path[:]
   for seg in capture[ref]['path']+[capture[ref]['uuid']]:f.proto.symbol_path.path.add().value=seg
  b.create_items(creates)
  # Native create can initially resolve names against existing net codes. Reassert.
  updates=[]
  for f in b.get_footprints():
   ref=f.reference_field.text.value
   if ref in MAP:
    for p in f.definition.pads:p.net=Net(name=MAP[ref].get(p.number) or '')
    updates.append(f)
  b.update_items(updates)
  texts=b.get_text();b.remove_items(texts)
  for text,x,y,layer in [('LCD / B2.25 pinout',81,60,BoardLayer.BL_F_SilkS),('GPIO LCD A2',80,64,BoardLayer.BL_F_SilkS),('1',55.5,75,BoardLayer.BL_F_SilkS),('5V/3V3 OPEN: close only for Pi-powered LCD',81,66,BoardLayer.BL_B_SilkS),('USB pins 1-4,6,7 not connected',81,68,BoardLayer.BL_B_SilkS)]:
   t=BoardText();t.value=text;t.position=Vector2.from_xy_mm(x,y);t.layer=layer;t.attributes.size=Vector2.from_xy_mm(.8,.8);t.attributes.stroke_width=120000;b.create_items([t])
  title=b.get_title_block_info();title.title='GPIO LCD bench adapter';title.revision='A2 B2.25';b.set_title_block_info(title);b.save()
  state={f.reference_field.text.value:dict(position=[f.position.x/1e6,f.position.y/1e6],rotation=f.orientation.degrees,pads={p.number:dict(net=p.net.name,xy=[p.position.x/1e6,p.position.y/1e6]) for p in f.definition.pads}) for f in b.get_footprints()}
 (D/'reports/native-migration.json').write_text(json.dumps(dict(pin_map=FFC,footprints=state,capture=capture),indent=2)+'\n')
 print('Created native A2 schematic and board; rerouting pending')
if __name__=='__main__':main()
