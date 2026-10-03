"""Real child-process reads/writes through each platform adapter, using a fake PE."""
import ctypes as C,json,mmap,os,pathlib,struct,subprocess,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))

def fixture():
 import backend
 build=backend.BUILD
 image=mmap.mmap(-1,build['image_size']);address=C.addressof(C.c_char.from_buffer(image))
 # Standalone synthetic header, not copied from an executable.
 image[:2]=b'MZ';image[60:64]=struct.pack('<I',128);image[128:132]=b'PE\0\0'
 image[132:134]=struct.pack('<H',0x8664);image[136:140]=struct.pack('<I',build['timestamp']);image[208:212]=struct.pack('<I',build['image_size'])
 for anchor in build['anchors']:
  data=bytes.fromhex(anchor['bytes']);image[anchor['rva']:anchor['rva']+len(data)]=data
 for p in build['height_patches']:image[p['rva']:p['rva']+2]=bytes.fromhex(p['original'])
 meta=mmap.mmap(-1,8192);base=C.addressof(C.c_char.from_buffer(meta));player=base+0x1000;appearance=base+0x800
 chain=build['player_chain']
 for key,offset in [('mode_global_rva',0),('career_global_rva',0x100),('roster_global_rva',0x200)]:image[chain[key]:chain[key]+8]=struct.pack('<Q',base+offset)
 meta[4:8]=struct.pack('<I',2);meta[0x210:0x214]=struct.pack('<I',1);meta[0x218:0x220]=struct.pack('<Q',player)
 meta[0x1000:0x100a]='Check'.encode('utf-16le');meta[0x1024:0x102c]='Kyle'.encode('utf-16le');meta[0x104c:0x1050]=struct.pack('<f',250);meta[0x1080:0x1088]=struct.pack('<Q',appearance);meta[0x10c9]=4
 for offset,value in [(0,213.36),(4,226.06),(0x60,1)]:meta[0x800+offset:0x804+offset]=struct.pack('<f',value)
 if os.name!='nt':
  libc=C.CDLL(None);protect=libc.mprotect;protect.argtypes=[C.c_void_p,C.c_size_t,C.c_int];protect.restype=C.c_int
  if protect(address,4096,1)!=0:raise RuntimeError('Fixture header protection failed')
 print(os.getpid(),flush=True)
 for line in sys.stdin:
  if line.strip()=='quit':break

class LiveMemoryTests(unittest.TestCase):
 def test_real_connection_write_and_undo(self):
  import backend,process_memory
  p=subprocess.Popen([sys.executable,str(pathlib.Path(__file__).resolve()),'--fixture'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  e=backend.Editor()
  try:
   line=p.stdout.readline().strip();self.assertTrue(line,'Fixture failed: '+p.stderr.read() if not line else '')
   pid=int(line)
   # Some sandbox tools expose host /proc alongside a nested PID namespace.
   if os.name!='nt':
    for entry in pathlib.Path('/proc').iterdir():
     if not entry.name.isdigit():continue
     try:
      ids=next(l.split()[1:] for l in (entry/'status').read_text().splitlines() if l.startswith('NSpid:'))
      if len(ids)>1 and int(ids[-1])==pid:pid=int(entry.name);break
     except (OSError,StopIteration):pass
   before=e.connect(pid);self.assertEqual(before['name'],'Kyle Check')
   changed=e.apply({'0':120,'1':150},True);self.assertEqual(changed['fields'][0]['value'],120);self.assertEqual(changed['fields'][1]['value'],150)
   self.assertEqual(e.patch_state(),1);self.assertEqual(e.restore(),before)
  finally:
   if e.fd is not None:e.release_patches();process_memory.close_process(e.fd)
   p.stdin.write('quit\n');p.stdin.flush();p.wait(timeout=5)
   p.stdin.close();p.stdout.close();p.stderr.close()
if __name__=='__main__':
 if '--fixture' in sys.argv:fixture()
 else:unittest.main()
