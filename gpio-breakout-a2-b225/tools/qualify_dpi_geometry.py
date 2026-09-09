"""Check every physical Pi pin through exactly one isolated series element."""
import json,xml.etree.ElementTree as ET
from qualify_power_paths import D,r,pads,path
# Physical Raspberry Pi header identities, independent of the edit mapping.
physical={'ID_SD':'27','ID_SC':'28','GPIO2':'3','GPIO3':'5','GPIO4':'7','GPIO5':'29','GPIO6':'31','GPIO7':'26','GPIO8':'24','GPIO9':'21','GPIO10':'19','GPIO11':'23','GPIO12':'32','GPIO13':'33','GPIO14':'8','GPIO15':'10','GPIO16':'36','GPIO17':'11','GPIO18':'12','GPIO19':'35','GPIO20':'38','GPIO21':'40'}
rows=[]
for net,header_pin in physical.items():
 start=('J2',header_pin);source_net=pads[start]['net']['name'];assert source_net==net+'_PI'
 matches=[(ref,pin) for (ref,pin),p in pads.items() if ref.startswith('RN') and p.get('net',{}).get('name')==source_net]
 assert len(matches)==1,(net,matches)
 ref,pin=matches[0];assert 1<=int(pin)<=4
 outpin=str(9-int(pin));assert pads[ref,outpin]['net']['name']==net
 finish=next(key for key,p in pads.items() if key[0]=='J1' and p.get('net',{}).get('name')==net)
 a=path(start,(ref,pin));z=path((ref,outpin),finish)
 rows.append({'net':net,'physical_pi_pin':header_pin,'FFC_pin':finish[1],'series_element':[ref,pin,outpin],
 'source_to_resistor_mm':a['path_length_mm'],'resistor_to_FFC_mm':z['path_length_mm'],
 'source_vias':a['through_vias'],'output_vias':z['through_vias']})
spares=[key for key,p in pads.items() if key[0].startswith('RN') and p.get('net',{}).get('name','').startswith('unconnected-')];assert len(spares)==4,spares
out={'source_board_sha256':r['board_sha256'],'driven_lines_checked':len(rows),'paths':rows,'source_series_components_present':True,
 'all_22_conductors_connected_through_exactly_one_isolated_element':len(rows)==22,'unused_array_pads_unconnected':len(spares),
 'fitted_value':'0 ohm provisions; nonzero fitted values require source/receiver timing qualification',
 'timing_status':'NOT MEASURED','required_inputs':['Pi model and GPIO drive settings','LCD/receiver mode and pixel clock','Actual catalog cable arrangement'],
 'source_length_range_mm':[min(v['source_to_resistor_mm'] for v in rows),max(v['source_to_resistor_mm'] for v in rows)],
 'total_planar_range_mm':[min(v['source_to_resistor_mm']+v['resistor_to_FFC_mm'] for v in rows),max(v['source_to_resistor_mm']+v['resistor_to_FFC_mm'] for v in rows)]}
(D/'reports/dpi-qualification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='paths'},indent=2))
