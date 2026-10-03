"""Small platform boundary: Linux /proc or Windows process-memory APIs."""
import os,pathlib
if os.name=='nt':
 from windows_memory import open_process,close_process,read_memory,write_memory,process_start,is_privileged,read_maps,processes
else:
 def open_process(pid):return os.open(f'/proc/{pid}/mem',os.O_RDWR)
 def close_process(handle):os.close(handle)
 def read_memory(handle,size,address):return os.pread(handle,size,address)
 def write_memory(handle,data,address):return os.pwrite(handle,data,address)
 def process_start(pid):return pathlib.Path(f'/proc/{pid}/stat').read_text().split(')')[-1].split()[19]
 def is_privileged():return os.geteuid()==0
 def read_maps(pid):
  out=[]
  for line in pathlib.Path(f'/proc/{pid}/maps').read_text().splitlines():
   p=line.split(maxsplit=5);lo,hi=[int(x,16) for x in p[0].split('-')]
   out.append((lo,hi,p[1],p[5] if len(p)>5 else '',int(p[2],16)))
  return out
 def processes():
  owner=int(os.environ.get('PKEXEC_UID',os.getuid()));rows=[]
  for p in pathlib.Path('/proc').iterdir():
   if not p.name.isdigit():continue
   try:
    status=(p/'status').read_text();uid=int(next(l for l in status.splitlines() if l.startswith('Uid:')).split()[1])
    if uid!=owner:continue
    comm=(p/'comm').read_text().strip();args=(p/'cmdline').read_bytes().decode(errors='replace').split('\0')
    exe=next((pathlib.PurePosixPath(a.strip(chr(34)).replace('\\','/')).name for a in args if a.strip(chr(34)).lower().endswith('.exe')),comm)
    likely='nba2k16' in ''.join(c for c in exe.lower() if c.isalnum());actual='nba2k16' in ''.join(c for c in comm.lower() if c.isalnum())
    rows.append(dict(pid=int(p.name),name=exe,comm=comm,likely=likely,actual_game=actual))
   except (OSError,ValueError,StopIteration):pass
  return sorted(rows,key=lambda r:(not r['actual_game'],not r['likely'],r['name'].lower(),r['pid']))
