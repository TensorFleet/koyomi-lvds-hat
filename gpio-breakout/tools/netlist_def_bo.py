"""GPIO breakout: FH41-40S FFC (carrier JDISP1/JFFC1 system) <-> Pi 40-pin header.

Straight-through pins 1..40 EXCEPT 17/34/39, which are isolated behind solder
jumpers: on a stock Pi those pins are 3V3/GND/GND, but the FFC system assigns
them PANEL_ID0/PANEL_ID1/LCD_INS. Jumpers default OPEN; test pads expose the
FFC-side nets for strapping or probing.
"""

NC = '__NC__'

# Pi header net names, physical pins 1..40 (standard map)
PI = {
    1: '+3V3', 2: '+5V', 3: 'GPIO2', 4: '+5V', 5: 'GPIO3', 6: 'GND',
    7: 'GPIO4', 8: 'GPIO14', 9: 'GND', 10: 'GPIO15', 11: 'GPIO17', 12: 'GPIO18',
    13: 'GPIO27', 14: 'GND', 15: 'GPIO22', 16: 'GPIO23', 17: '+3V3', 18: 'GPIO24',
    19: 'GPIO10', 20: 'GND', 21: 'GPIO9', 22: 'GPIO25', 23: 'GPIO11', 24: 'GPIO8',
    25: 'GND', 26: 'GPIO7', 27: 'ID_SD', 28: 'ID_SC', 29: 'GPIO5', 30: 'GND',
    31: 'GPIO6', 32: 'GPIO12', 33: 'GPIO13', 34: 'GND', 35: 'GPIO19', 36: 'GPIO16',
    37: 'GPIO26', 38: 'GPIO20', 39: 'GND', 40: 'GPIO21',
}
SPECIAL = {17: 'PANEL_ID0', 34: 'PANEL_ID1', 39: 'LCD_INS'}

ffc_map = {}
for n in range(1, 41):
    ffc_map[str(n)] = SPECIAL.get(n, PI[n])
ffc_map['1'] = '+3V3_FFC'
ffc_map['2'] = '+5V_FFC'
ffc_map['4'] = '+5V_FFC'
for n in range(41, 50):          # shield / mounting pins
    ffc_map[str(n)] = 'GND'

hdr_map = {str(n): PI[n] for n in range(1, 41)}

COMPONENTS = [
    ('J1', 'B2_INTERCONNECT:FH41-40S-0.5SH', 'FH41-40S-0.5SH(05)',
     'B2_INTERCONNECT:FPC-SMD_FH41-40S-0.5SH', ffc_map,
     {'lcsc': 'C596805', 'desc': 'carrier/LCD system FFC, bottom contact'}),
    ('J2', 'Connector_Generic:Conn_02x20_Odd_Even', 'Pi GPIO 2x20',
     'Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical', hdr_map,
     {'desc': 'fit stacking socket to ride a Pi, or pin header for cables'}),
    ('JP1', 'Jumper:SolderJumper_2_Open', 'ID0-3V3',
     'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm',
     {'1': 'PANEL_ID0', '2': '+3V3'}, {'desc': 'close = FFC17 to Pi 3V3 (STRAP HIGH)'}),
    ('JP2', 'Jumper:SolderJumper_2_Open', 'ID1-GND',
     'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm',
     {'1': 'PANEL_ID1', '2': 'GND'}, {'desc': 'close = FFC34 to GND (STRAP LOW)'}),
    ('JP3', 'Jumper:SolderJumper_2_Open', 'INS-GND',
     'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm',
     {'1': 'LCD_INS', '2': 'GND'}, {'desc': 'close = FFC39 to GND (report inserted)'}),
    ('F1', 'Device:Polyfuse', '0.5A polyfuse 1206',
     'Fuse:Fuse_1206_3216Metric', {'1': '+5V_LNK', '2': '+5V_FFC'},
     {'lcsc': 'C106264', 'desc': 'PTC resettable, 0.5 A hold — FFC contact rating (SMD1206P050TF/15; alt C315893)'}),
    ('JP4', 'Jumper:SolderJumper_2_Bridged', '5V LINK',
     'Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm',
     {'1': '+5V', '2': '+5V_LNK'}, {'desc': 'CUT when LCD chain is powered externally'}),
    ('JP5', 'Jumper:SolderJumper_2_Bridged', '3V3 LINK',
     'Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm',
     {'1': '+3V3', '2': '+3V3_FFC'}, {'desc': 'CUT when LCD chain is powered externally'}),
    ('TP1', 'Connector:TestPoint', 'PANEL_ID0',
     'TestPoint:TestPoint_Pad_1.5x1.5mm', {'1': 'PANEL_ID0'}, {}),
    ('TP2', 'Connector:TestPoint', 'PANEL_ID1',
     'TestPoint:TestPoint_Pad_1.5x1.5mm', {'1': 'PANEL_ID1'}, {}),
    ('TP3', 'Connector:TestPoint', 'LCD_INS',
     'TestPoint:TestPoint_Pad_1.5x1.5mm', {'1': 'LCD_INS'}, {}),
    ('TP4', 'Connector:TestPoint', 'GND',
     'TestPoint:TestPoint_Pad_1.5x1.5mm', {'1': 'GND'}, {}),
    ('TP5', 'Connector:TestPoint', '3V3',
     'TestPoint:TestPoint_Pad_1.5x1.5mm', {'1': '+3V3'}, {}),
    ('H1', 'Mechanical:MountingHole', 'M2.5',
     'MountingHole:MountingHole_2.7mm_M2.5', None, {}),
    ('H2', 'Mechanical:MountingHole', 'M2.5',
     'MountingHole:MountingHole_2.7mm_M2.5', None, {}),
]

PWR_FLAGS = [
    ('#FLG1', '+3V3'), ('#FLG2', '+5V'), ('#FLG3', 'GND'),
]
