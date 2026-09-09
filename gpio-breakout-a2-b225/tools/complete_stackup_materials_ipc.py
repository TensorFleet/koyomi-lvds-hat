"""Set JLC mask dielectric approximation through KiCad's stackup command."""
import json
from update_addon_ipc import session,D
from kipy.proto.board import board_commands_pb2
from google.protobuf.json_format import MessageToDict
with session(D/'gpio_breakout.kicad_pcb') as k:
 b=k.get_board();s=b.get_stackup().proto
 for layer in s.layers:
  if layer.HasField('soldermask'):
   layer.thickness.value_nm=15240;layer.soldermask.thickness.value_nm=15240;layer.soldermask.epsilon_r=3.8
   layer.soldermask.material_name='JLC soldermask; 15.24 um above trace; substrate/gap 30.48 um'
 cmd=board_commands_pb2.UpdateBoardStackup();cmd.board.CopyFrom(b.document);cmd.stackup.CopyFrom(s)
 response=b._kicad.send(cmd,board_commands_pb2.BoardStackupResponse);b.save()
 print(json.dumps(MessageToDict(response,preserving_proto_field_name=True),indent=2))
