"""Synthetic player memory exercises field edits without redistributing game code."""
import unittest,struct,sys,pathlib
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import backend,ui_values
class Memory:
 def __init__(self):self.bytes={}
 def read(self,handle,n,a):return bytes(self.bytes.get(a+i,0) for i in range(n))
 def write(self,handle,data,a):
  for i,b in enumerate(data):self.bytes[a+i]=b
  return len(data)
class EditorTests(unittest.TestCase):
 def setUp(self):
  self.m=Memory();self.e=backend.Editor();e=self.e;e.fd=1;e.pid=123;e.start=77;e.base=0x10000;e.image=0x100000;e.appearance=0x20000
  e.current_player=lambda:e.base
  self.m.write(1,'Check'.encode('utf-16le'),e.base);self.m.write(1,'Kyle'.encode('utf-16le'),e.base+0x24)
  self.m.write(1,struct.pack('<f',250),e.base+0x4c);self.m.write(1,struct.pack('<Q',e.appearance),e.base+0x80)
  for off,value in [(0,213.36),(4,226.06),(0x60,1)]:self.m.write(1,struct.pack('<f',value),e.appearance+off)
  for p in backend.BUILD['height_patches']:self.m.write(1,bytes.fromhex(p['original']),e.image+p['rva'])
  e.identity=self.m.read(1,72,e.base)
  self.patches=[patch.object(backend,'read_memory',self.m.read),patch.object(backend,'write_memory',self.m.write),patch.object(backend,'process_start',lambda pid:77)]
  for p in self.patches:p.start()
  self.addCleanup(lambda:[p.stop() for p in reversed(self.patches)])
 def test_height_and_undo(self):
  before=self.e.state();after=self.e.apply({'0':120,'1':150},True)
  self.assertEqual(after['fields'][0]['value'],120);self.assertEqual(after['fields'][1]['value'],150);self.assertEqual(self.e.patch_state(),1)
  self.assertEqual(self.e.restore(),before);self.assertEqual(self.e.patch_state(),0)
 def test_badges_and_attribute_bulk_preserve_unrelated_bits(self):
  before=self.e.state();changes={}
  for f in before['fields']:
   if f['group'] in ('Attributes','Badges'):changes[str(f['id'])]=max(map(int,f['options'])) if f.get('options') else (1<<f['bits'])-1
  after=self.e.apply(changes,True)
  for f in after['fields']:
   if str(f['id']) in changes:self.assertEqual(f['value'],changes[str(f['id'])])
   else:self.assertEqual(f['value'],before['fields'][f['id']]['value'])
  self.assertEqual(self.e.restore(),before)
 def test_stale_player_and_bounds(self):
  for changes in ({'0':121},{'1':151},{'0':float('nan')}):
   with self.assertRaises(ValueError):self.e.apply(changes,True)
  self.m.write(1,struct.pack('<Q',0),self.e.base+0x80)
  with self.assertRaises(RuntimeError):self.e.apply({'0':120},True)
 def test_height_format(self):
  self.assertEqual(ui_values.format_height(95),'7′ 11″');self.assertEqual(ui_values.format_height(120),'10′ 0″')
  self.assertEqual(backend.FIELDS[0]['step'],1);self.assertEqual(backend.FIELDS[1]['step'],1)
if __name__=='__main__':unittest.main()
