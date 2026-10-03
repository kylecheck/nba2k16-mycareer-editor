#!/usr/bin/env python3
"""Native desktop UI. Tk when installed, X11 fallback without extra packages."""
import os,sys,pathlib,json,subprocess,threading,queue,time,traceback
ROOT=pathlib.Path(getattr(sys,'_MEIPASS',pathlib.Path(__file__).resolve().parent))
DATA_ROOT=pathlib.Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else ROOT
class Controller:
 def __init__(self):
  self.generation=0;self.queue=queue.Queue();self.proc=None;self.busy=False;self.ready=False;self.privileged=False
  self.status='Starting editor...';self.rows=[];self.selected=None;self.data=None;self.original={};self.values={};self.confirmed=False;self.log=[];self.closing=False
  self.start()
 def start(self,elevated=False):
  if self.busy:return
  if elevated and os.name=='nt':
   import ctypes
   shell=ctypes.WinDLL('shell32',use_last_error=True);execute=shell.ShellExecuteW
   execute.restype=ctypes.c_void_p;execute.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_int]
   args=None if getattr(sys,'frozen',False) else subprocess.list2cmdline([str(ROOT/'app.py')])
   result=execute(None,'runas',sys.executable,args,str(DATA_ROOT),1)
   if result and result>32:self.closing=True;self.close()
   else:self.status='Administrator restart cancelled or denied.'
   return
  if self.proc and self.proc.poll() is None:
   self.proc.stdin.write('{"action":"quit"}\n');self.proc.stdin.flush();self.proc.wait(timeout=3)
  self.generation+=1;generation=self.generation
  cmd=[sys.executable,'--backend'] if getattr(sys,'frozen',False) else [sys.executable,str(ROOT/'backend.py')]
  if elevated:cmd=['pkexec']+cmd
  self.ready=False;self.data=None;self.confirmed=False;self.original={};self.values={}
  self.status='Approve the system memory-access prompt...' if elevated else 'Starting process reader...'
  try:
   self.proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',bufsize=1,cwd=ROOT,creationflags=0x08000000 if os.name=='nt' else 0)
   def reader(proc):
    for line in proc.stdout:
     try:self.queue.put(dict(json.loads(line),generation=generation))
     except Exception:self.queue.put({'event':'error','message':line.strip(),'generation':generation})
    self.queue.put({'event':'exit','code':proc.wait(),'error':proc.stderr.read()[-2000:],'generation':generation})
   threading.Thread(target=reader,args=(self.proc,),daemon=True).start()
  except Exception as e:self.status=str(e)
 def send(self,action,**kwargs):
  if self.busy or not self.ready:return
  if action=='connect':self.data=None;self.confirmed=False;self.values={};self.original={}
  self.busy=True;self.status={'connect':'Connecting to selected game...','processes':'Refreshing process list...','apply':'Applying changes...'}.get(action,'Reading player...')
  self.proc.stdin.write(json.dumps(dict(action=action,**kwargs))+'\n');self.proc.stdin.flush()
 def refresh(self):self.send('processes')
 def connect(self):
  if self.selected is None:self.status='Choose NBA 2K16 in the process list first.';return
  self.send('connect',pid=self.selected)
 def apply(self):
  if not self.data:self.status='Connect and read your player first.';return
  try:changes={str(k):float(v) for k,v in self.values.items() if float(v)!=self.original[k]}
  except ValueError:self.status='Enter numeric values in the fields.';return
  if not changes:self.status='No changed values.';return
  self.send('apply',changes=changes,confirmed=True)
 def bulk(self,group):
  if self.busy:return
  if not self.data:self.status='Connect and read your player first.';return
  count=0
  for f in self.data['fields']:
   if f['group']!=group or not f.get('enabled',True):continue
   maximum=max(map(int,f['options'])) if f.get('options') else (1<<f['bits'])-1
   self.values[f['id']]=str(maximum);count+=1
  self.status=f'{count} {group.lower()} staged at maximum. Press Apply changes to write them; Undo restores the previous values.'
 def poll(self):
  changed=False
  while not self.queue.empty():
   r=self.queue.get()
   if r.get('generation')!=self.generation:continue
   changed=True;self.log.append(r)
   if r['event']=='ready':self.ready=True;self.privileged=r['privileged'];self.refresh()
   elif r['event']=='progress':self.status=r['message']
   elif r['event']=='exit':
    self.ready=False;self.busy=False;self.status='Editor backend closed. '+r.get('error','')
   elif r['event']=='error':self.status=r['message']
   elif r['event']=='result':
    self.busy=False
    if not r['ok']:self.status=r['error'];continue
    a=r['action'];d=r['data']
    if a=='processes':
     self.rows=d
     if self.selected not in [x['pid'] for x in d]:self.selected=next((x['pid'] for x in d if x['likely']),None)
     self.status=f'{len(d)} user processes found. Select NBA 2K16, then Connect.'
    else:
     self.data=d;self.original={f['id']:f['value'] for f in d['fields']};self.values={f['id']:str(f['value']) for f in d['fields']}
     self.status='Player: '+d['name']+(' | Changes read back.' if a=='apply' else ' | Ready to edit.')
  return changed
 def close(self):
  if self.busy:self.status='Finishing connection cleanup before closing...';self.closing=True;return False
  if self.proc and self.proc.poll() is None:
   self.proc.stdin.write('{"action":"quit"}\n');self.proc.stdin.flush()
  return True

def tk_ui(c):
 from themed_ui import run
 run(c)
if __name__=='__main__':
 if '--self-test' in sys.argv:
  import backend,process_memory
  assert backend.FIELDS and backend.BUILD['height_patches']
  import tkinter
  assert isinstance(process_memory.processes(),list)
  sys.exit(0)
 if '--backend' in sys.argv:
  from backend import worker
  worker();sys.exit(0)
 c=Controller()
 try:
  try:import tkinter
  except ImportError:tkinter=None
  if tkinter is not None:tk_ui(c)
  else:
   from native_x11 import run
   run(c)
 except Exception:
  (DATA_ROOT/'startup-error.txt').write_text(traceback.format_exc());print(traceback.format_exc(),file=sys.stderr)
 finally:
  if not c.busy:c.close()
