"""Restore 1:1 paste on J1 only; require unchanged electrical geometry."""
import copy,hashlib,json,sys
from pathlib import Path
from update_addon_ipc import session,D
from kipy.board_types import BoardLayer
from google.protobuf.json_format import MessageToDict
DESC='Samtec ZF5S-40-01-T-WT-K-TR, 40-position 0.5 mm bottom-contact FFC; manufacturer land/stencil drawing Rev E, 1:1 paste apertures'
def stable(d):
 if isinstance(d,dict):
  result={k:stable(v) for k,v in d.items() if k != "parent"}
  if 'custom_shapes' in result:
   for shape in result['custom_shapes']:shape.pop('id',None)
  return result
 if isinstance(d,list):return [stable(v) for v in d]
 return d
def normalized(f):
 d=MessageToDict(f.proto,preserving_proto_field_name=True)
 if f.reference_field.text.value=='J1':
  d['definition']['attributes']['description']=''
  for item in d['definition']['items']:
   if item['@type'].endswith('.Pad'):
    item['pad_stack']['layers']=[l for l in item['pad_stack']['layers'] if l!='BL_F_Paste']
 return stable(d)
def capture(b):return {'footprints':{f.id.value:normalized(f) for f in b.get_footprints()},'tracks':{t.id.value:stable(MessageToDict(t.proto,preserving_proto_field_name=True)) for t in [*b.get_tracks(),*b.get_vias()]}}
p=D/'gpio_breakout.kicad_pcb';baseline=Path(sys.argv[1]) if len(sys.argv)>1 else p;before=hashlib.sha256(baseline.read_bytes()).hexdigest()
with session(baseline) as k:old=capture(k.get_board())
with session(p) as k:
 b=k.get_board();assert capture(b)==old;f=next(f for f in b.get_footprints() if f.reference_field.text.value=='J1');pads=list(f.definition.pads);assert len(pads)==42
 n=sum(BoardLayer.BL_F_Paste in p.padstack.layers for p in pads)
 assert n in (0,42)
 for pad in pads:
  assert BoardLayer.BL_F_Cu in pad.padstack.layers
  sizes=pad.padstack.copper_layers[0].size
  assert (sizes.x,sizes.y)==((300000,1600000) if pad.number else (2240000,3120000))
  if BoardLayer.BL_F_Paste not in pad.padstack.layers:pad.padstack.layers=[*pad.padstack.layers,BoardLayer.BL_F_Paste]
 f.definition.proto.attributes.description=DESC;b.update_items([f]);after=capture(b)
 if after!=old:
  differences={key:{id:{'before':v,'after':after[key].get(id)} for id,v in entries.items() if after[key].get(id)!=v} for key,entries in old.items()};(D/'reports/j1-paste-candidate-diff.json').write_text(json.dumps(differences,indent=2,default=str));raise RuntimeError('Unexpected native normalization; candidate not saved')
 b.save()
with session(p) as k:
 b=k.get_board();fresh=capture(b)
 if fresh!=old:
  differences={key:{id:{'before':v,'after':fresh[key].get(id)} for id,v in entries.items() if fresh[key].get(id)!=v} for key,entries in old.items()};(D/'reports/j1-paste-reload-diff.json').write_text(json.dumps(differences,indent=2,default=str));raise RuntimeError('Inspect saved reload comparison')
 f=next(f for f in b.get_footprints() if f.reference_field.text.value=='J1');pads=list(f.definition.pads);assert all(BoardLayer.BL_F_Paste in p.padstack.layers for p in pads)
result={'passed':True,'before_sha256':before,'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'paste_pad_count':len(pads),'signal_pads':40,'mounting_pads':2,'all_tracks_vias_and_normalized_footprints_unchanged':True,'normalization':'Exclude intended J1 paste/description, session document parent IDs and generated IDs of custom-pad primitive shapes; retain geometry and pad/item IDs.','description':DESC,'stencil_thickness':'Samtec drawing Rev E specifies 0.15 mm; product specification 6.3 says 0.13 mm. Reconcile with assembler before release.','fabrication_generated':False}
(D/'reports/j1-paste-repair.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
