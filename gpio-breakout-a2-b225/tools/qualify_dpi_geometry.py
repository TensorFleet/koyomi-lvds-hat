"""Desktop DPI topology screen; timing qualification needs actual source and panel."""
import json
from qualify_power_paths import D,r,pads,path
nets=['ID_SC','GPIO2','GPIO3','ID_SD']+[f'GPIO{i}' for i in range(4,22)];rows=[]
for net in nets:
 a=next(k for k,p in pads.items() if k[0]=='J2' and p.get('net',{}).get('name')==net)
 z=next(k for k,p in pads.items() if k[0]=='J1' and p.get('net',{}).get('name')==net)
 result=path(a,z);rows.append({k:result[k] for k in ('from','to','net','path_length_mm','through_vias')})
out={'source_board_sha256':r['board_sha256'],'driven_lines_checked':len(rows),'paths':rows,'source_series_components_present':False,'physical_topology':'Direct J2-to-J1 paths; no source-side series resistance on GPIO A2. The C1 RN201-RN206 arrays are at the receiving board.','timing_status':'NOT QUALIFIED','required_inputs':['Raspberry Pi model and configured drive strength/slew','LCD panel mode/pixel clock and receiver timing','installed catalog cable length/contact arrangement'],'next_design_action':'Provision source-side series resistors near J2 after the Pi/panel assumptions are identified; choose fitted values with driver impedance/channel analysis. A 0-ohm fitting supplies an option, not termination. Coordinate receiver-side C1 arrays so a second resistance is not added unintentionally.','hardware_checks':['Scope clock and worst data lines at the C1 receiver at target pixel clock; measure setup/hold, overshoot and undershoot.','Exercise full pattern and power sequencing with the actual panel.'],'all_22_conductors_connected':len(rows)==22}
(D/'reports/dpi-qualification.json').write_text(json.dumps(out,indent=2)+'\n');print('DPI paths:',len(rows),'range',min(p['path_length_mm'] for p in rows),max(p['path_length_mm'] for p in rows),'mm; source/panel timing qualification pending.')
