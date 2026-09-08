"""Rebuild local Samtec library through KiCad's native footprint serializer.
Input is the native IPC snapshot, never a parsed or rewritten KiCad S-expression.
Preserve pad numbering/local geometry, 2D segments and the nominal model.
"""
import json,hashlib,tempfile,shutil
from pathlib import Path
import pcbnew as p
D=Path(__file__).resolve().parents[1]
r=json.loads((D/'reports/manufacturing-findings-native.json').read_text());f=r['j1'];assert f['orientation']['value_degrees']==180
origin=f['position']
def vec(v):return p.VECTOR2I(int(origin['x_nm'])-int(v.get('x_nm',0)),int(origin['y_nm'])-int(v.get('y_nm',0)))
def size(v):return p.VECTOR2I(int(v['x_nm']),int(v['y_nm']))
name=f['definition']['id']['entry_name'];fp=p.FOOTPRINT(None);fp.SetFPIDAsString('VAIO_CM5:'+name);fp.SetAttributes(p.FP_SMD)
fp.SetReference('REF**');fp.SetValue('ZF5S-40-01-T-WT-K-TR');fp.SetLibDescription('Samtec ZF5S-40-01-T-WT-K-TR; manufacturer Rev E land pattern and 1:1 paste apertures; nominal envelope model only')
for key,target in [('reference_field',fp.Reference()),('value_field',fp.Value())]:
 text=f[key]['text']['text'];target.SetPosition(vec(text['position']));target.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));target.SetTextSize(size(text['attributes']['size']));target.SetLayer(p.F_SilkS if key=='reference_field' else p.F_Fab)
expected=[];graphics=0
for item in f['definition']['items']:
 kind=item['@type'].split('.')[-1]
 if kind=='Pad':
  pad=p.PAD(fp);pad.SetNumber(item.get('number',''));pad.SetAttribute(p.PAD_ATTRIB_SMD);stack=item['pad_stack'];cl=stack['copper_layers'];assert len(cl)==1 and cl[0]['shape']=='PSS_RECTANGLE'
  pad.SetShape(p.PAD_SHAPE_RECT);pad.SetSize(size(cl[0]['size']));pad.SetPosition(vec(item['position']));layers=p.LSET();layers.AddLayer(p.F_Cu);layers.AddLayer(p.F_Paste);layers.AddLayer(p.F_Mask);pad.SetLayerSet(layers);pad.SetOrientation(p.EDA_ANGLE(0,p.DEGREES_T));fp.Add(pad)
  expected.append((pad.GetNumber(),pad.GetPosition().x,pad.GetPosition().y,pad.GetSize().x,pad.GetSize().y))
 elif kind=='BoardGraphicShape':
  shape=item['shape'];assert 'segment' in shape;g=p.PCB_SHAPE(fp);g.SetShape(p.SHAPE_T_SEGMENT);g.SetStart(vec(shape['segment']['start']));g.SetEnd(vec(shape['segment']['end']));g.SetWidth(int(shape['attributes']['stroke']['width']['value_nm']));g.SetLayer({'BL_F_SilkS':p.F_SilkS,'BL_F_Fab':p.F_Fab,'BL_F_CrtYd':p.F_CrtYd}[item['layer']]);fp.Add(g);graphics+=1
 elif kind=='Footprint3DModel':
  assert item['rotation']=={} and item['offset']=={};model=p.FP_3DMODEL();model.m_Filename=item['filename'];fp.Models().push_back(model)
 elif kind=='Field':
  assert item['name']=='LCSC';field=p.PCB_FIELD(fp,p.FIELD_T_USER,'LCSC');field.SetText('C3169111');field.SetVisible(False);fp.Add(field)
 else:raise RuntimeError(kind)
assert len(expected)==42 and graphics==9
target=D/'VAIO_CM5.pretty';work=tempfile.TemporaryDirectory(prefix='samtec-native-',dir='/private/tmp');lib=Path(work.name)/'Samtec.pretty';lib.mkdir();p.PCB_IO_KICAD_SEXPR().FootprintSave(str(lib),fp)
loaded=p.FootprintLoad(str(lib),name);assert loaded
actual=[(q.GetNumber(),q.GetPosition().x,q.GetPosition().y,q.GetSize().x,q.GetSize().y) for q in loaded.Pads()]
assert sorted(actual)==sorted(expected);assert all(q.GetLayerSet().Contains(p.F_Paste) for q in loaded.Pads());assert len(loaded.Models())==1
shutil.copy2(lib/(name+'.kicad_mod'),target/(name+'.kicad_mod'))
out={'passed':True,'native_serializer':p.GetBuildVersion(),'pads':42,'graphics':graphics,'pad_geometry_matches_native_snapshot':True,'paste_apertures':'1:1, default local paste margins','library_sha256':hashlib.sha256((lib/(name+'.kicad_mod')).read_bytes()).hexdigest(),'model':'Preserved nominal envelope; still not a detailed mating model'}
(D/'reports/j1-library-repair.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
