"""64-bit Windows adapter. No injection, drivers or third-party libraries."""
import ctypes as C,os,pathlib
from ctypes import wintypes as W
if os.name!='nt':raise ImportError('Windows process APIs require Windows.')
if C.sizeof(C.c_void_p)!=8:raise RuntimeError('Use 64-bit Python or the Windows x64 release.')
k=C.WinDLL('kernel32',use_last_error=True)
SIZE=C.c_size_t;HANDLE=W.HANDLE;PTR=C.c_void_p;DWORD=W.DWORD
class ProcessEntry(C.Structure):
 _fields_=[('dwSize',DWORD),('cntUsage',DWORD),('th32ProcessID',DWORD),('th32DefaultHeapID',SIZE),('th32ModuleID',DWORD),('cntThreads',DWORD),('th32ParentProcessID',DWORD),('pcPriClassBase',W.LONG),('dwFlags',DWORD),('szExeFile',W.WCHAR*260)]
class MemoryInfo(C.Structure):
 _fields_=[('BaseAddress',PTR),('AllocationBase',PTR),('AllocationProtect',DWORD),('PartitionId',W.WORD),('RegionSize',SIZE),('State',DWORD),('Protect',DWORD),('Type',DWORD)]
def api(name,result,args):
 f=getattr(k,name);f.restype=result;f.argtypes=args;return f
Open=api('OpenProcess',HANDLE,[DWORD,W.BOOL,DWORD]);Close=api('CloseHandle',W.BOOL,[HANDLE])
Read=api('ReadProcessMemory',W.BOOL,[HANDLE,PTR,PTR,SIZE,C.POINTER(SIZE)])
Write=api('WriteProcessMemory',W.BOOL,[HANDLE,PTR,PTR,SIZE,C.POINTER(SIZE)])
Protect=api('VirtualProtectEx',W.BOOL,[HANDLE,PTR,SIZE,DWORD,C.POINTER(DWORD)])
Query=api('VirtualQueryEx',SIZE,[HANDLE,PTR,C.POINTER(MemoryInfo),SIZE])
Flush=api('FlushInstructionCache',W.BOOL,[HANDLE,PTR,SIZE])
Times=api('GetProcessTimes',W.BOOL,[HANDLE,C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME)])
Snapshot=api('CreateToolhelp32Snapshot',HANDLE,[DWORD,DWORD])
First=api('Process32FirstW',W.BOOL,[HANDLE,C.POINTER(ProcessEntry)]);Next=api('Process32NextW',W.BOOL,[HANDLE,C.POINTER(ProcessEntry)])
def check(ok):
 if not ok:raise C.WinError(C.get_last_error())
def open_process(pid):
 h=Open(0x400|0x10|0x20|0x8,False,int(pid))
 if not h:
  if C.get_last_error()==5:raise PermissionError('Access denied. Restart the editor as administrator.')
  raise C.WinError(C.get_last_error())
 return h
def close_process(handle):check(Close(handle))
def process_start(pid):
 h=Open(0x1000,False,int(pid))
 if not h:raise FileNotFoundError('Game closed. Connect again.')
 try:
  creation,exit,kernel,user=(W.FILETIME() for _ in range(4));check(Times(h,C.byref(creation),C.byref(exit),C.byref(kernel),C.byref(user)))
  if exit.dwHighDateTime or exit.dwLowDateTime:raise FileNotFoundError('Game closed. Connect again.')
  # A retained handle can still exist after exit; opening by PID and creation
  # time guards against PID reuse and reattachment to another process.
  return (creation.dwHighDateTime<<32)|creation.dwLowDateTime
 finally:Close(h)
def read_memory(handle,size,address):
 data=C.create_string_buffer(size);count=SIZE();check(Read(handle,address,data,size,C.byref(count)))
 return data.raw[:count.value]
def write_memory(handle,data,address):
 info=MemoryInfo();check(Query(handle,address,C.byref(info),C.sizeof(info)))
 old=DWORD();changed=not bool(info.Protect&(0x04|0x08|0x40|0x80))
 if changed:check(Protect(handle,address,len(data),0x40,C.byref(old)))
 try:
  buffer=C.create_string_buffer(data);count=SIZE();check(Write(handle,address,buffer,len(data),C.byref(count)))
  check(Flush(handle,address,len(data)));return count.value
 finally:
  if changed:
   ignored=DWORD();check(Protect(handle,address,len(data),old.value,C.byref(ignored)))
def read_maps(pid):
 h=Open(0x400,False,int(pid));check(h);out=[];address=0
 try:
  while address<0x0000800000000000:
   info=MemoryInfo()
   if not Query(h,address,C.byref(info),C.sizeof(info)):break
   lo=info.BaseAddress or 0;end=lo+info.RegionSize
   if end<=address:break
   if info.State==0x1000 and not info.Protect&(0x100|0x01):
    out.append((lo,end,'r--p','',0))
   address=end
 finally:Close(h)
 return out
def processes():
 h=Snapshot(2,0)
 if h==PTR(-1).value:raise C.WinError(C.get_last_error())
 rows=[]
 try:
  entry=ProcessEntry();entry.dwSize=C.sizeof(entry);ok=First(h,C.byref(entry))
  while ok:
   name=entry.szExeFile;likely='nba2k16' in ''.join(c for c in name.lower() if c.isalnum())
   if entry.th32ProcessID:rows.append(dict(pid=entry.th32ProcessID,name=name,comm=name,likely=likely,actual_game=likely))
   ok=Next(h,C.byref(entry))
 finally:Close(h)
 return sorted(rows,key=lambda r:(not r['likely'],r['name'].lower(),r['pid']))
def is_privileged():
 shell=C.WinDLL('shell32',use_last_error=True);f=shell.IsUserAnAdmin;f.restype=W.BOOL;f.argtypes=[]
 return bool(f())
