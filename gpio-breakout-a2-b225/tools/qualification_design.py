"""Explicit circuit additions for GPIO A2 bench qualification."""
ARRAYS={
 'RN1':['GPIO2','GPIO3','GPIO4','GPIO14'],
 'RN2':['GPIO15','GPIO17','GPIO18',None],
 'RN3':['GPIO10','GPIO9','GPIO11','GPIO8'],
 'RN4':['GPIO7','ID_SD','ID_SC',None],
 'RN5':['GPIO5','GPIO6','GPIO12','GPIO13'],
 'RN6':['GPIO19','GPIO16','GPIO20','GPIO21'],
}
DRIVEN={n for group in ARRAYS.values() for n in group if n}
EXTRA_MAP={'U4':{'1':'USB_VBUS_IN','2':'GND','3':'USB_VBUS_IN','4':'USB_SLEW_CT','5':None,'6':'USB_VBUS_SOFT'},
           'C3':{'1':'USB_SLEW_CT','2':'GND'},'C4':{'1':'USB_VBUS_SOFT','2':'GND'}}
for ref,group in ARRAYS.items():
 EXTRA_MAP[ref]={str(i+1):(n+'_PI' if n else None) for i,n in enumerate(group)}
 EXTRA_MAP[ref].update({str(8-i):n for i,n in enumerate(group)})
POSITIONS={'U4':(105.55,52.5,90),'C1':(101,55.5,0),'C3':(105.55,55.35,0),'C4':(100,58,0),
 'RN1':(62,75,270),'RN2':(69.6,75,270),'RN3':(82.3,75,270),
 'RN4':(89.9,75,270),'RN5':(96,75,270),'RN6':(103,75,270)}
