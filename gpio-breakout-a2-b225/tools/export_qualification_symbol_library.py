"""Package KiCad's already-serialized cached symbol into a project library.

The symbol body is copied verbatim from the native schematic output. Only the
library-qualified root name is converted to its library entry name. No native
board or schematic source is modified. Run kicad-cli sym upgrade afterwards.
"""
from pathlib import Path
D=Path(__file__).resolve().parents[1]
s=(D/'gpio_breakout.kicad_sch').read_text();needle='(symbol "GPIO_Qualification:TPS22918DBV"';start=s.index(needle);level=0;quoted=False;escaped=False;end=None
for i,c in enumerate(s[start:],start):
 if quoted:
  if escaped:escaped=False
  elif c=='\\':escaped=True
  elif c=='"':quoted=False
 elif c=='"':quoted=True
 elif c=='(':level+=1
 elif c==')':
  level-=1
  if level==0:end=i+1;break
assert end is not None
symbol=s[start:end].replace(needle,'(symbol "TPS22918DBV"',1)
(D/'GPIO_Qualification.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "native_cache_packager")\n'+symbol+'\n)\n')
p=D/'sym-lib-table';table=p.read_text()
last=table.rfind(')')
if 'GPIO_Qualification' not in table:p.write_text(table[:last]+'\n (lib (name "GPIO_Qualification") (type "KiCad") (uri "${KIPRJMOD}/GPIO_Qualification.kicad_sym") (options "") (descr "TPS22918 from the verified native circuit definition"))\n'+table[last:])
print('Packaged native cached TPS22918 definition; native library validation pending.')
