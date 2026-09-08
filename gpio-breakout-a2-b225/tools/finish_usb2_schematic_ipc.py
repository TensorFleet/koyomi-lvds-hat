"""Ground the standard SH shield contact and correct retained power-link descriptions."""
from update_addon_ipc import session,sheets,pins,D
from kipy.schematic_types import GlobalLabel
from kipy.proto.common.types.enums_pb2 import KiCadObjectType
from kipy.geometry import Vector2
with session(D/'gpio_breakout.kicad_sch') as k:
 root,ss=sheets(k);s=ss[0];fps={f.reference_field.text.value:f for f in s.get_symbols()}
 pin=pins(fps['J3'])['SH'];point=(pin.position.x_nm,pin.position.y_nm)
 markers=s.get_items([KiCadObjectType.KOT_SCH_NO_CONNECT])
 s.remove_items([x for x in markers if (x.position.x,x.position.y)==point])
 l=GlobalLabel();l.text.value='GND';l.position=Vector2(pin.position);l.text.position=Vector2(pin.position)
 l.text.attributes.size=Vector2.from_xy_mm(.9,.9);s.create_items([l])
 for ref,text in {'JP4':'Normally open Pi 5V to F1 and LCD FFC9/10 link; close only for a single Pi-powered LCD source',
                  'JP5':'Normally open Pi 3V3 to LCD FFC11 link; close only for a single Pi-powered LCD source'}.items():
  fps[ref].description_field.text.value=text
 s.update_items([fps['JP4'],fps['JP5']]);s.save();root.save()
print('Native shell ground and power-link descriptions corrected.')
