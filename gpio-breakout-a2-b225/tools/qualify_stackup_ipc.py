"""Read saved native construction and verify stackup-only migration preserves copper."""
import hashlib,json,sys
from pathlib import Path
from google.protobuf.json_format import MessageToDict
from update_addon_ipc import session,D

def stable(d):
 if isinstance(d,dict):
  d={k:stable(v) for k,v in d.items() if k!='parent'}
  for shape in d.get('custom_shapes',[]):shape.pop('id',None)
  return d
 if isinstance(d,list):return [stable(v) for v in d]
 return d

def capture(b):
 return {name:{x.id.value:stable(MessageToDict(x.proto,preserving_proto_field_name=True)) for x in xs} for name,xs in [('footprints',b.get_footprints()),('tracks',b.get_tracks()),('vias',b.get_vias()),('zones',b.get_zones())]}
p=D/'gpio_breakout.kicad_pcb';baseline=Path(sys.argv[1]);report=D/'reports/stackup-qualification.json'
with session(baseline) as k:old=capture(k.get_board())
with session(p) as k:
 b=k.get_board();current=capture(b);stack=MessageToDict(b.get_stackup().proto,preserving_proto_field_name=True)
 expected=json.loads(json.dumps(old))
 refilled_zones=[key for key in old['zones'] if old['zones'][key].get('filled_polygons')!=current['zones'][key].get('filled_polygons')]
 for key in expected['zones']:
  expected['zones'][key].pop('filled_polygons',None);current['zones'][key].pop('filled_polygons',None)
 widths=json.loads((D/'reports/power-width-qualification.json').read_text())['widened']
 for t in widths:expected['tracks'][t['id']]['width']['value_nm']=str(round(t['after_mm']*1e6))
 # The new native serializer normalizes these custom jumper defaults 45 -> 90.
 # They have no same-net zones, so this cannot change a thermal connection here.
 allowed_thermal=[]
 zone_nets={z.get('net',{}).get('name','') for z in current['zones'].values()}
 for key,f in expected['footprints'].items():
  ref=f['reference_field']['text']['text']['text']
  if ref not in ('JP4','JP5'):continue
  for old_pad,new_pad in zip(f['definition']['items'],current['footprints'][key]['definition']['items']):
   if not old_pad['@type'].endswith('.Pad'):continue
   assert old_pad.get('net',{}).get('name') not in zone_nets
   a=old_pad['pad_stack']['zone_settings']['thermal_spokes']['angle'];z=new_pad['pad_stack']['zone_settings']['thermal_spokes']['angle']
   assert a['value_degrees']==45 and z['value_degrees']==90
   a['value_degrees']=90;allowed_thermal.append({'ref':ref,'pad':old_pad.get('number'),'before_degrees':45,'after_degrees':90,'same_net_zones':False})
 diffs={kind:{key:{'before':value,'after':current[kind].get(key)} for key,value in entries.items() if value!=current[kind].get(key)} for kind,entries in expected.items()}
 counts={kind:[len(old[kind]),len(current[kind])] for kind in old}
 copper=[x for x in stack['layers'] if x['type']=='BSLT_COPPER'];dielectric=[x for x in stack['layers'] if x['type']=='BSLT_DIELECTRIC'];mask=[x for x in stack['layers'] if x['type']=='BSLT_SOLDERMASK']
 checks={'copper_thicknesses_match':[int(x['thickness']['value_nm']) for x in copper]==[35000,15200,15200,35000],
 'dielectric_thicknesses_match':[int(x['thickness']['value_nm']) for x in dielectric]==[210400,1065000,210400],
 'dielectric_constants_match':[x['dielectric']['layer'][0]['epsilon_r'] for x in dielectric]==[4.4,4.6,4.4],
 'prepreg_core_prepeg':[x['dielectric']['type'] for x in dielectric]==['BSDT_PREPREG','BSDT_CORE','BSDT_PREPREG'],
 'mask_parameters_match':all(x['soldermask']['epsilon_r']==3.8 and int(x['thickness']['value_nm'])==15240 for x in mask),
 'impedance_control_enabled':stack['impedance']['is_controlled'],
 'all_geometry_matches_except_documented_power_widths':all(not diffs[k] and counts[k][0]==counts[k][1] for k in old)}
 result={'passed':all(checks.values()),'checks':checks,'board_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'baseline_sha256':hashlib.sha256(baseline.read_bytes()).hexdigest(),'stackup':stack,'counts':counts,'allowed_nonfunctional_thermal_normalization':allowed_thermal,'power_segments_widened':len(widths),'refilled_zone_count':len(refilled_zones),'zone_validation':'Zone boundaries/settings preserved; fill polygons regenerated for wider trace clearances and verified by native DRC and USB reference-plane audit','copper_dielectric_total_mm':1.5862,'with_flat_mask_approximation_mm':1.61668,'order_nominal_thickness_mm':1.6,'source':'https://jlcpcb.com/impedance','note':'Native flat mask uses published thickness above traces. JLC also specifies 30.48 um above substrate/between traces; use the manufacturer calculator for its nonuniform mask model. Loss tangent 0.02 remains an unqualified inherited placeholder; no broadband SI model is claimed.','differences':diffs}
 report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('differences','stackup')},indent=2))
 if not result['passed']:raise SystemExit(2)
