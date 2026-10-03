"""Small native X11 UI fallback for SteamOS builds without Tk installed."""
import ctypes as C, ctypes.util, time, textwrap
P=C.c_void_p;U=C.c_ulong;I=C.c_int
class Event(C.Union):_fields_=[('type',I),('pad',C.c_long*24)]
class Input(C.Structure):
 _fields_=[('type',I),('serial',U),('send_event',I),('display',P),('window',U),('root',U),('subwindow',U),('time',U),('x',I),('y',I),('x_root',I),('y_root',I),('state',C.c_uint),('code',C.c_uint),('same_screen',I)]
class Configure(C.Structure):
 _fields_=[('type',I),('serial',U),('send_event',I),('display',P),('event',U),('window',U),('x',I),('y',I),('width',I),('height',I),('border_width',I),('above',U),('override',I)]
class FontHead(C.Structure):_fields_=[('ext_data',P),('fid',U)]
def run(c):
 x=C.CDLL(ctypes.util.find_library('X11') or 'libX11.so.6')
 def bind(n,result,args):
  f=getattr(x,n);f.restype=result;f.argtypes=args;return f
 open_display=bind('XOpenDisplay',P,[C.c_char_p]);d=open_display(None)
 if not d:raise RuntimeError('No desktop display. Run this editor in Steam Deck Desktop Mode.')
 screen=bind('XDefaultScreen',I,[P])(d);root=bind('XRootWindow',U,[P,I])(d,screen)
 window=bind('XCreateSimpleWindow',U,[P,U,I,I,C.c_uint,C.c_uint,C.c_uint,U,U])(d,root,20,20,1100,740,0,0,0x101112)
 gc=bind('XCreateGC',P,[P,U,U,P])(d,window,0,None)
 bind('XStoreName',I,[P,U,C.c_char_p])(d,window,b'NBA 2K16 MyCareer Editor')
 bind('XSelectInput',I,[P,U,C.c_long])(d,window,(1<<15)|(1<<17)|1|4|(1<<6))
 atom=bind('XInternAtom',U,[P,C.c_char_p,I])(d,b'WM_DELETE_WINDOW',0);atoms=(U*1)(atom)
 bind('XSetWMProtocols',I,[P,U,C.POINTER(U),I])(d,window,atoms,1)
 loadfont=bind('XLoadQueryFont',P,[P,C.c_char_p]);font=loadfont(d,b'9x15') or loadfont(d,b'fixed')
 if font:bind('XSetFont',I,[P,P,U])(d,gc,C.cast(font,C.POINTER(FontHead)).contents.fid)
 bind('XMapWindow',I,[P,U])(d,window)
 foreground=bind('XSetForeground',I,[P,P,U]);fill=bind('XFillRectangle',I,[P,U,P,I,I,C.c_uint,C.c_uint]);string=bind('XDrawString',I,[P,U,P,I,I,C.c_char_p,I]);flush=bind('XFlush',I,[P]);pending=bind('XPending',I,[P]);next_event=bind('XNextEvent',I,[P,C.POINTER(Event)]);lookup=bind('XLookupString',I,[C.POINTER(Input),P,I,C.POINTER(U),P])
 width,height=1100,740;tab='Processes';page=0;focus=None;last_data=None;targets=[];running=True;sliders=[];drag=None
 def rect(a,b,w,h,color):foreground(d,gc,color);fill(d,window,gc,a,b,max(1,w),max(1,h))
 def text(a,b,s,color=0xf5f5f2):
  foreground(d,gc,color);s=str(s).encode('latin-1','replace');string(d,window,gc,a,b,s,len(s))
 def button(a,b,w,h,label,fn,selected=False):
  rect(a,b,w,h,0xf4f4ee if selected else 0x292c2d);text(a+12,b+h//2+5,label,0x141515 if selected else 0xf5f5f2);targets.append((a,b,w,h,fn))
 def choose(pid):c.selected=pid
 def switch(name):
  nonlocal tab,page,focus
  tab=name;page=0;focus=None
 def edit(i,delta):
  nonlocal focus
  f=next(f for f in c.data['fields'] if f['id']==i);maximum=f.get('max',max(map(int,f['options'])) if f.get('options') else (1<<f['bits'])-1);minimum=f.get('min',0)
  try:v=float(c.values[i])
  except ValueError:v=minimum
  c.values[i]=str(round(max(minimum,min(maximum,v+delta*f.get('step',1))),4));focus=None
 def focusfield(i):
  nonlocal focus
  focus=i
 def move(delta):
  nonlocal page,focus
  page=max(0,page+delta);focus=None
 def draw():
  nonlocal targets,page,sliders
  targets=[];sliders=[];rect(0,0,width,height,0x101112)
  text(22,32,'NBA 2K16 MyCareer Editor');text(22,58,'Load MyCareer, select NBA 2K16, then Connect.',0xa4a6a4)
  button(20,76,172,44,'Refresh processes',c.refresh);button(202,76,130,44,'Connect',c.connect)
  button(342,76,225,44,'Enable memory access',lambda:c.start(True))
  for i,line in enumerate(textwrap.wrap(c.status,max(40,(width-40)//9))[:3]):text(22,145+i*20,line,0xe0df19)
  for i,name in enumerate(['Processes','Player','Attributes','Badges']):button(20+i*180,202,170,42,name,lambda name=name:switch(name),tab==name)
  rowheight=46;count=max(3,(height-430)//rowheight);items=c.rows if tab=='Processes' else [f for f in (c.data or {'fields':[]})['fields'] if f['group']==tab]
  lastpage=max(0,(len(items)-1)//count);page=min(page,lastpage)
  if tab=='Processes':text(22,269,'PID      Application / EXE                           Process name',0xa4a6a4)
  elif not c.data:text(22,280,'Connect to your player first.')
  elif tab=='Attributes':text(22,269,'Raw attribute bytes; displayed rating conversion is unverified.',0xa4a6a4)
  else:text(22,269,'Player: '+c.data['name'],0xa4a6a4)
  for j,item in enumerate(items[page*count:(page+1)*count]):
   y=286+j*rowheight
   if tab=='Processes':button(20,y,width-40,rowheight-5,f"{item['pid']:<8} {item['name'][:40]:<40} {item['comm'][:22]}",lambda pid=item['pid']:choose(pid),c.selected==item['pid'])
   else:
    f=item;i=f['id'];text(28,y+27,f['name'][:max(16,(width-(600 if f.get('source')=='appearance' else 410))//9)])
    value=c.values[i]
    if f.get('display')=='feet_inches':
     from ui_values import format_height
     value=format_height(value)
    if f.get('options'):value=f['options'].get(str(int(float(value))),value)
    if f.get('source')=='appearance' and f.get('enabled',True):
     sx=width-570;sw=220
     rect(sx,y+17,sw,6,0x292c2d)
     fraction=max(0,min(1,(float(c.values[i])-f['min'])/(f['max']-f['min'])))
     rect(sx+int(fraction*sw)-5,y+7,10,26,0xe0df19)
     sliders.append((sx,y,sw,38,f))
    button(width-330,y,48,38,'-',lambda i=i:edit(i,-1))
    button(width-272,y,150,38,value[:14],lambda i=i:focusfield(i),focus==i)
    button(width-112,y,48,38,'+',lambda i=i:edit(i,1))
  y=height-140
  button(20,y,125,38,'Previous',lambda:move(-1));text(166,y+25,f'Page {page+1} / {lastpage+1}');button(330,y,110,38,'Next',lambda:move(1))
  if tab in ('Attributes','Badges'):button(460,y,240,38,'Max attributes' if tab=='Attributes' else 'All badges (Gold)',lambda:c.bulk(tab))
  button(20,height-48,150,38,'Read values',lambda:c.send('refresh'));button(180,height-48,160,38,'Apply changes',c.apply);button(350,height-48,180,38,'Undo last apply',lambda:c.send('undo'))

  flush(d)
 def slide(ev,slider):
  sx,sy,sw,sh,f=slider
  value=f['min']+max(0,min(1,(ev.x-sx)/sw))*(f['max']-f['min'])
  c.values[f['id']]=str(round(round((value-f['min'])/f['step'])*f['step']+f['min'],4))
 def handle_key(ev):
  nonlocal focus
  buf=C.create_string_buffer(32);key=U();n=lookup(C.byref(ev),buf,32,C.byref(key),None)
  if key.value==0xff1b:focus=None;return
  if focus is None or not c.data:return
  f=next(f for f in c.data['fields'] if f['id']==focus)
  if key.value in (0xff0d,0xff8d):focus=None
  elif key.value==0xff08:c.values[focus]=c.values[focus][:-1]
  elif key.value==0xffff:c.values[focus]=''
  elif key.value==0xff52:edit(focus,1)
  elif key.value==0xff54:edit(focus,-1)
  elif not f.get('options'):
   s=buf.raw[:n].decode('ascii',errors='ignore')
   if all(ch in '0123456789.' for ch in s) and len(c.values[focus])+len(s)<12:c.values[focus]+=s
 try:
  draw()
  while running:
   dirty=c.poll()
   if c.data is not last_data:
    if c.data:tab='Player';page=0
    last_data=c.data;dirty=True
   if c.closing and not c.busy:running=False;c.close();continue
   while pending(d):
    e=Event();next_event(d,C.byref(e));dirty=True
    if e.type==33:
     if c.close():running=False
    elif e.type==22:
     cfg=C.cast(C.byref(e),C.POINTER(Configure)).contents;width=max(760,cfg.width);height=max(580,cfg.height)
    elif e.type==6:
     if drag and C.cast(C.byref(e),C.POINTER(Input)).contents.state&256:slide(C.cast(C.byref(e),C.POINTER(Input)).contents,drag)
    elif e.type==4:
     ev=C.cast(C.byref(e),C.POINTER(Input)).contents
     if ev.code in (4,5):move(-1 if ev.code==4 else 1)
     elif ev.code==1:
      drag=None
      for slider in sliders:
       a,b,w,h,f=slider
       if a<=ev.x<a+w and b<=ev.y<b+h:drag=slider;slide(ev,slider);break
      for a,b,w,h,fn in targets:
       if a<=ev.x<a+w and b<=ev.y<b+h:fn();break
    elif e.type==2:handle_key(C.cast(C.byref(e),C.POINTER(Input)).contents)
   if dirty:draw()
   time.sleep(.035)
 finally:bind('XCloseDisplay',I,[P])(d)
