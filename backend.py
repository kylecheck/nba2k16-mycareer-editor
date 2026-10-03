#!/usr/bin/env python3
"""Linux x86-64 NBA 2K16 editor. Standard library only."""
import os, pathlib, json, struct, sys, traceback, math
ROOT=pathlib.Path(getattr(sys,'_MEIPASS',pathlib.Path(__file__).resolve().parent))
from process_memory import open_process,close_process,read_memory,write_memory,process_start,is_privileged,read_maps,processes
FIELDS=json.loads((ROOT/'fields.json').read_text()); BUILD=json.loads((ROOT/'build.json').read_text())
class Editor:
 def __init__(self):self.pid=None;self.fd=None;self.base=None;self.identity=None;self.start=None;self.undo=None;self.image=None;self.details={};self.appearance=None;self.owned_patches={}
 def read(self,a,n):
  b=read_memory(self.fd,n,a)
  if len(b)!=n:raise RuntimeError('Incomplete memory read')
  return b
 def valid(self):
  if not self.base:raise RuntimeError("Connect to your MyCareer player first.")
  if not self.pid or process_start(self.pid)!=self.start:raise RuntimeError('Game restarted. Connect again.')
  if self.image is not None and self.current_player()!=self.base:raise RuntimeError("Active MyCareer player changed. Connect again.")
  if self.identity!=self.read(self.base,72):raise RuntimeError('Player changed. Connect again.')
 def connect(self,pid,progress=lambda s:None):
  if self.fd is not None:self.release_patches();close_process(self.fd)
  self.fd=None;self.base=None;self.identity=None;self.undo=None;self.image=None;self.details={}
  self.appearance=None;self.owned_patches={}
  self.pid=int(pid)
  progress(f"Opening selected process {self.pid}")
  try:self.start=process_start(self.pid)
  except OSError:raise RuntimeError('Selected process has closed. Refresh processes and select the game again.')
  try:self.fd=open_process(self.pid)
  except PermissionError:raise RuntimeError('ACCESS DENIED: select Enable memory access, approve the system prompt, then Connect again.')
  progress('Reading process memory regions and locating the loaded Windows game image')
  maps=read_maps(self.pid);images=[];denied=0
  # Proton can map the PE image anonymously. Detect PE headers in process memory,
  # rather than requiring an NBA2K16.exe filename in /proc/PID/maps.
  for lo,hi,perms,path,off in maps:
   if 'r' not in perms or hi-lo<4096:continue
   try:
    head=self.read(lo,min(4096,hi-lo))
    if head[:2]!=b'MZ':continue
    pe=struct.unpack_from('<I',head,60)[0]
    if not 64<=pe<=3072 or head[pe:pe+4]!=b'PE\0\0':continue
    machine=struct.unpack_from('<H',head,pe+4)[0]
    timestamp=struct.unpack_from('<I',head,pe+8)[0]
    size=struct.unpack_from('<I',head,pe+24+56)[0]
    if machine==0x8664 and timestamp==BUILD['timestamp'] and size==BUILD['image_size']:
     if all(self.read(lo+a['rva'],len(bytes.fromhex(a['bytes'])))==bytes.fromhex(a['bytes']) for a in BUILD['anchors']):images.append(lo)
   except (OSError,ValueError,struct.error):denied+=1
  images=list(set(images))
  if len(images)!=1:
   raise RuntimeError(f'Game process opened, but found {len(images)} matching NBA2K16 memory images. Select the actual game EXE, not Steam/wineserver. If the correct process is selected, report the error and your game build. Unreadable regions: {denied}.')
  self.image=images[0]
  progress('Reading the active MyCareer player directly from the game pointer chain')
  self.base=self.current_player()
  self.identity=self.read(self.base,72)
  weight=struct.unpack('<f',self.read(self.base+0x4c,4))[0]
  if not 50<weight<1000 or (self.read(self.base+0xc9,1)[0]&7)>4:
   self.base=None;raise RuntimeError('Direct player pointer did not contain plausible player data. Report this error before trying edits.')
  self.appearance=struct.unpack("<Q",self.read(self.base+BUILD["appearance_pointer_offset"],8))[0]
  if not 0<self.appearance<0x0000800000000000:self.appearance=None
  return self.state()
 def current_player(self):
  # Same lookup executed by NBA2K16.exe RVA 0x1128A0, as called by the
  # old table's hook. Globals were derived from RIP-relative instructions.
  chain=BUILD['player_chain'];details={}
  def unpack(fmt,addr):return struct.unpack(fmt,self.read(addr,struct.calcsize(fmt)))[0]
  def ptr(addr):
   value=unpack('<Q',addr)
   if not 0<value<0x0000800000000000:raise RuntimeError('Game pointer is not initialized. Load MyCareer and Connect again.')
   return value
  try:
   mode_object=ptr(self.image+chain['mode_global_rva']);mode=unpack('<I',mode_object+4);details['mode']=mode
   if mode!=2:raise RuntimeError(f'Game is not in MyCareer mode (mode {mode}). Load your MyCareer, then Connect.')
   career=ptr(self.image+chain['career_global_rva']);index=unpack('<H',career);details['player_index']=index
   roster=ptr(self.image+chain['roster_global_rva']);count=unpack('<I',roster+0x10);details['roster_count']=count
   if index==0xffff or not 0<count<=100000 or index>=count:raise RuntimeError('Current MyCareer player index is not loaded. Load your save and reconnect.')
   players=ptr(roster+0x18);base=players+index*chain['player_stride']
   # Repeat the selector to reject a load transition mid-read.
   if ptr(self.image+chain['career_global_rva'])!=career or unpack('<H',career)!=index or ptr(self.image+chain['roster_global_rva'])!=roster or ptr(roster+0x18)!=players:raise RuntimeError('Player data changed during lookup. Wait for loading to finish, then reconnect.')
   details['lookup']='direct';self.details=details;return base
  except Exception:
   self.details=details;raise
 def appearance_address(self,f):
  current=struct.unpack('<Q',self.read(self.base+BUILD['appearance_pointer_offset'],8))[0]
  if not self.appearance or current!=self.appearance:raise RuntimeError('Appearance data changed or is not loaded. Reconnect from your MyCareer gym.')
  return self.appearance+f['offset']
 def patch_state(self):
  states=[]
  for p in BUILD['height_patches']:
   data=self.read(self.image+p['rva'],2)
   if data==bytes.fromhex(p['original']):states.append(0)
   elif data==bytes.fromhex(p['patched']):states.append(1)
   else:raise RuntimeError('Height-limit code was changed by another tool. Close other trainers and restart the game.')
  if len(set(states))!=1:raise RuntimeError('Height-limit overrides are inconsistent. Restart the game before editing.')
  return states[0]
 def release_patches(self):
  if not self.owned_patches:return
  try:
   same=process_start(self.pid)==self.start
   if same:
    for a,original in self.owned_patches.items():
     if self.read(a,1)==b'\xeb':
      if write_memory(self.fd,original,a)!=1:raise RuntimeError('Could not restore height limit')
  except FileNotFoundError:pass
  finally:self.owned_patches={}
 def state(self):
  self.valid();out=[]
  for i,f in enumerate(FIELDS):
   enabled=True
   if f.get('source')=='height_unlock':v=self.patch_state()
   elif f.get('source')=='appearance' and self.appearance is None:v=0;enabled=False
   else:
    a=self.appearance_address(f) if f.get('source')=='appearance' else self.base+f['offset']
    n=4 if f['type']=='Float' else (f['bit']+f['bits']+7)//8
    b=self.read(a,n)
    v=struct.unpack('<f',b)[0]/f.get('factor',1) if f['type']=='Float' else (int.from_bytes(b,'little')>>f['bit'])&((1<<f['bits'])-1)
    if f.get('source')=='appearance':
     if not math.isfinite(v):raise RuntimeError('Appearance contains invalid numbers. Report this error.')
     v=round(v,4)
   out.append(dict(f,id=i,value=v,enabled=enabled))
  name=lambda o:self.read(self.base+o,32).decode('utf-16le',errors='replace').split('\0')[0]
  return dict(name=name(0x24)+' '+name(0),fields=out)
 def apply(self,changes,confirmed):
  self.valid()
  if not confirmed:raise RuntimeError('Confirm the displayed player first.')
  plan={};unlock=None;height_changed=False
  for k,v in changes.items():
   i=int(k)
   if not 0<=i<len(FIELDS):raise ValueError('Invalid field')
   f=FIELDS[i];v=float(v)
   if not math.isfinite(v):raise ValueError('Enter a finite number for '+f['name'])
   if f.get('options') and (not v.is_integer() or str(int(v)) not in f['options']):raise ValueError('Invalid choice for '+f['name'])
   if f.get('source')=='height_unlock':unlock=int(v);continue
   a=self.appearance_address(f) if f.get('source')=='appearance' else self.base+f['offset']
   if f['type']=='Float':
    lo=f.get('min',50);hi=f.get('max',1000)
    if not lo<=v<=hi:raise ValueError(f"{f['name']} must be {lo}–{hi}")
    data=struct.pack('<f',v*f.get('factor',1))
    if f.get('source')=='appearance' and f['offset']==0:height_changed=True
   else:
    if not v.is_integer() or not 0<=v<=((1<<f['bits'])-1):raise ValueError('Value outside field range')
    n=(f['bit']+f['bits']+7)//8
    old=bytes(plan.get(a+j,self.read(a+j,1)[0]) for j in range(n))
    mask=((1<<f['bits'])-1)<<f['bit'];data=((int.from_bytes(old,'little')&~mask)|(int(v)<<f['bit'])).to_bytes(n,'little')
   for j,b in enumerate(data):plan[a+j]=b
  if height_changed and unlock is None:unlock=1
  new_owned=dict(self.owned_patches)
  if unlock is not None:
   self.patch_state()
   for p in BUILD['height_patches']:
    a=self.image+p['rva'];original=bytes.fromhex(p['original']);patched=bytes.fromhex(p['patched']);current=self.read(a,2)
    if unlock and current==original:new_owned[a]=original[:1]
    # Only the single-byte short-branch opcode changes; displacement stays intact.
    plan[a]=(patched if unlock else original)[0]
    if not unlock:new_owned.pop(a,None)
  before={a:self.read(a,1) for a in plan};old_owned=dict(self.owned_patches)
  previous_undo=self.undo;written=[]
  try:
   for a,b in plan.items():
    if write_memory(self.fd,bytes([b]),a)!=1:raise RuntimeError('Incomplete memory write')
    written.append(a)
   if any(self.read(a,1)!=bytes([b]) for a,b in plan.items()):raise RuntimeError('Game overwrote a value; changes rolled back')
   self.owned_patches=new_owned
   result=self.state();self.undo=(before,old_owned);return result
  except Exception as failure:
   errors=[]
   for a in reversed(written):
    try:
     if write_memory(self.fd,before[a],a)!=1:errors.append('Incomplete rollback')
    except OSError as e:errors.append(str(e))
   self.owned_patches=old_owned;self.undo=previous_undo
   if errors:raise RuntimeError(str(failure)+'; rollback issue: '+'; '.join(errors)) from failure
   raise
 def restore(self):
  self.valid()
  if self.undo is None:raise RuntimeError('No edits to undo')
  before,owned=self.undo
  for a,b in before.items():
   if write_memory(self.fd,b,a)!=1:raise RuntimeError('Incomplete undo write')
  self.owned_patches=owned;self.undo=None;return self.state()

def worker():
 editor=Editor()
 emit=lambda r:print(json.dumps(r,allow_nan=False),flush=True)
 emit({'event':'ready','privileged':is_privileged()})
 for line in sys.stdin:
  try:
   req=json.loads(line);action=req['action']
   progress=lambda s:emit({'event':'progress','message':s})
   if action=='processes':data=processes()
   elif action=='connect':data=editor.connect(req['pid'],progress)
   elif action=='refresh':data=editor.state()
   elif action=='apply':data=editor.apply(req['changes'],req.get('confirmed',False))
   elif action=='undo':data=editor.restore()
   elif action=='quit':break
   else:raise ValueError('Unknown action')
   emit({'event':'result','action':action,'ok':True,'data':data})
  except Exception as e:emit({'event':'result','action':req.get('action','unknown') if 'req' in locals() else 'unknown','ok':False,'error':str(e),'traceback':traceback.format_exc()})
 if editor.fd is not None:editor.release_patches();close_process(editor.fd)
if __name__=='__main__':worker()
