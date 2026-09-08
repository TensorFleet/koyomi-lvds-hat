"""GPIO A2 USB2 extension, retaining every LCD/Pi connection."""
from update_addon_ipc import FFC as LCD_FFC, MAP as LCD_MAP, PI
FFC={**LCD_FFC,**{str(n):'USB_VBUS' for n in (1,2,3,4)},'6':'USB_D_N','7':'USB_D_P'}
USB_CONNECTOR={p:None for p in [f'{r}{n}' for r in 'AB' for n in range(1,13)]+['SH']}
USB_CONNECTOR.update({p:'GND' for p in ('A1','A12','B1','B12','SH')})
USB_CONNECTOR.update({p:'USB_VBUS_RAW' for p in ('A4','A9','B4','B9')})
USB_CONNECTOR.update({'A5':'USB_CC1','B5':'USB_CC2','A6':'USB_D_P','B6':'USB_D_P','A7':'USB_D_N','B7':'USB_D_N'})
MAP={**LCD_MAP,'J1':FFC,'J3':USB_CONNECTOR,
 'F2':{'1':'USB_VBUS_RAW','2':'USB_VBUS_IN'},
 'U1':{'1':'USB_VBUS_IN','2':'GND','3':'USB_VBUS','4':None,'5':'GND','6':'USB_VBUS'},
 'U2':{'1':'USB_D_P','2':'USB_D_N','3':'GND'},
 'U3':{'1':'USB_CC1','2':'USB_CC2','3':'GND'},
 'R1':{'1':'USB_CC1','2':'GND'},'R2':{'1':'USB_CC2','2':'GND'},
 'C1':{'1':'USB_VBUS_IN','2':'GND'},'C2':{'1':'USB_VBUS','2':'GND'},
 '#FLG4':{'1':'USB_VBUS_RAW'},'#FLG5':{'1':'USB_VBUS_IN'}}
FOOTPRINTS={'J3':'USB_A2:USB_C_Receptacle_Molex_105450-0101',
 'U1':'Package_TO_SOT_SMD:SOT-363_SC-70-6',
 'U2':'Package_TO_SOT_SMD:Texas_DRT-3','U3':'Package_TO_SOT_SMD:Texas_DRT-3',
 'R1':'Resistor_SMD:R_0603_1608Metric','R2':'Resistor_SMD:R_0603_1608Metric',
 'C1':'Capacitor_SMD:C_0603_1608Metric','C2':'Capacitor_SMD:C_0603_1608Metric',
 'F2':'Fuse:Fuse_1206_3216Metric'}
VALUES={'J3':'1054500101','U1':'LM66100DCKR','U2':'TPD2EUSB30DRTR','U3':'TPD2EUSB30DRTR',
 'R1':'5.1k 1%','R2':'5.1k 1%','C1':'1u 16V X7R','C2':'100n 16V X7R','F2':'SMD1206P050TF/15'}
