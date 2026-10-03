"""Real Windows API smoke tests; skipped on Linux. No NBA 2K16 required."""
import os,unittest,ctypes as C,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
@unittest.skipUnless(os.name=='nt','Requires Windows x64')
class WindowsMemoryTests(unittest.TestCase):
 def test_read_write_process_enumeration_and_creation_time(self):
  import windows_memory as m
  buffer=C.create_string_buffer(b'NBA2K16 fixture');address=C.addressof(buffer);h=m.open_process(os.getpid())
  try:
   self.assertEqual(m.read_memory(h,7,address),b'NBA2K16')
   self.assertEqual(m.write_memory(h,b'Editor!',address),7);self.assertEqual(buffer.raw[:7],b'Editor!')
   self.assertEqual(m.process_start(os.getpid()),m.process_start(os.getpid()))
   self.assertTrue(any(p['pid']==os.getpid() for p in m.processes()))
   self.assertTrue(any(lo<=address<hi for lo,hi,*_ in m.read_maps(os.getpid())))
  finally:m.close_process(h)
 def test_executable_page_write_restores_protection(self):
  import windows_memory as m
  allocate=m.api('VirtualAlloc',C.c_void_p,[C.c_void_p,m.SIZE,m.DWORD,m.DWORD])
  free=m.api('VirtualFree',C.c_int,[C.c_void_p,m.SIZE,m.DWORD])
  address=allocate(None,4096,0x3000,0x40);self.assertTrue(address)
  h=m.open_process(os.getpid())
  try:
   C.memmove(address,b'\x75\x27',2);old=m.DWORD();m.check(m.Protect(h,address,4096,0x20,C.byref(old)))
   self.assertEqual(m.write_memory(h,b'\xeb',address),1);self.assertEqual(m.read_memory(h,2,address),b'\xeb\x27')
   info=m.MemoryInfo();m.check(m.Query(h,address,C.byref(info),C.sizeof(info)));self.assertEqual(info.Protect,0x20)
  finally:m.close_process(h);m.check(free(address,0,0x8000))
if __name__=='__main__':unittest.main()
