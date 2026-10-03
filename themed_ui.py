"""Native settings-menu interface inspired by the user's NBA 2K references."""
import os
import tkinter as tk
from tkinter import ttk
from ui_values import format_height
BG='#101112';PANEL='#17191a';ROW='#191b1c';ALT='#141617';TEXT='#f5f5f2';MUTED='#a4a6a4';YELLOW='#e0df19';WHITE='#f4f4ee';INK='#141515'
def run(c):
 root=tk.Tk();root.title('NBA 2K16 | MyCareer Editor');root.geometry('1100x760');root.minsize(860,640);root.configure(bg=BG)
 style=ttk.Style(root);style.theme_use('clam')
 style.configure('.',font=('DejaVu Sans',12),background=BG,foreground=TEXT)
 style.configure('TFrame',background=BG);style.configure('TLabel',background=BG,foreground=TEXT)
 style.configure('TNotebook',background=BG,borderwidth=0)
 style.configure('TNotebook.Tab',background=PANEL,foreground=TEXT,padding=(21,11),borderwidth=0)
 style.map('TNotebook.Tab',background=[('selected',WHITE)],foreground=[('selected',INK)])
 style.configure('Treeview',background=PANEL,fieldbackground=PANEL,foreground=TEXT,rowheight=35,borderwidth=0)
 style.configure('Treeview.Heading',background=WHITE,foreground=INK,font=('DejaVu Sans',11,'bold'))
 style.map('Treeview',background=[('selected',WHITE)],foreground=[('selected',INK)])
 style.configure('Vertical.TScrollbar',background='#484a48',troughcolor=BG,borderwidth=0,arrowcolor=TEXT)
 root.option_add('*TCombobox*Listbox.background',PANEL);root.option_add('*TCombobox*Listbox.foreground',TEXT)
 shell=tk.Frame(root,bg=BG);shell.pack(fill='both',expand=True,padx=22,pady=16)
 header=tk.Frame(shell,bg=BG);header.pack(fill='x')
 tk.Label(header,text='2K',bg='#bc1928',fg=WHITE,font=('DejaVu Sans',28,'bold'),padx=9).pack(side='left')
 titles=tk.Frame(header,bg=BG);titles.pack(side='left',padx=14)
 tk.Label(titles,text='MYCAREER EDITOR',bg=BG,fg=TEXT,font=('DejaVu Sans',23,'bold')).pack(anchor='w')
 tk.Label(titles,text='NBA 2K16  /  WINDOWS PREVIEW' if os.name=='nt' else 'NBA 2K16  /  STEAM DECK',bg=BG,fg=MUTED,font=('DejaVu Sans',10,'bold')).pack(anchor='w',pady=3)
 tk.Frame(shell,bg=YELLOW,height=3).pack(fill='x',pady=(12,12))
 def button(parent,label,command,primary=False):
  return tk.Button(parent,text=label,command=command,bg=YELLOW if primary else '#292c2d',fg=INK if primary else TEXT,activebackground=WHITE,activeforeground=INK,relief='flat',bd=0,padx=14,pady=8,font=('DejaVu Sans',11,'bold'),cursor='hand2')
 top=tk.Frame(shell,bg=BG);top.pack(fill='x')
 for label,command in [('REFRESH PROCESSES',c.refresh),('CONNECT',c.connect),('ENABLE MEMORY ACCESS',lambda:c.start(True))]:button(top,label,command).pack(side='left',padx=(0,8))
 status=tk.StringVar(value=c.status)
 tk.Label(shell,textvariable=status,bg=BG,fg=YELLOW,anchor='w',justify='left',wraplength=1000,font=('DejaVu Sans',11)).pack(fill='x',pady=(10,12))
 notebook=ttk.Notebook(shell);notebook.pack(fill='both',expand=True)
 pages={}
 for name in ('Processes','Player','Attributes','Badges'):
  page=tk.Frame(notebook,bg=BG);notebook.add(page,text=name.upper());pages[name]=page
 tree=ttk.Treeview(pages['Processes'],columns=('pid','name','comm'),show='headings')
 for key,width,title in [('pid',90,'PID'),('name',360,'APPLICATION / GAME'),('comm',260,'PROCESS NAME')]:tree.heading(key,text=title);tree.column(key,width=width)
 tree.pack(fill='both',expand=True,pady=12)
 tree.bind('<<TreeviewSelect>>',lambda _:setattr(c,'selected',int(tree.selection()[0])) if tree.selection() else None)
 tk.Label(pages['Processes'],text='Load MyCareer in your gym, select NBA2K16.exe, then Connect.',bg=BG,fg=MUTED,anchor='w').pack(fill='x',pady=(0,8))
 footer=tk.Frame(shell,bg=BG);footer.pack(fill='x')
 for label,command,primary in [('READ VALUES',lambda:c.send('refresh'),False),('APPLY CHANGES',c.apply,True),('UNDO LAST APPLY',lambda:c.send('undo'),False)]:button(footer,label,command,primary).pack(side='left',padx=(0,8))
 footer.pack_forget();notebook.pack_forget()
 footer.pack(side='bottom',fill='x',pady=(12,0));notebook.pack(fill='both',expand=True)
 variables={};canvases={};paint=[];chosen=[None]
 def select_row(index):
  chosen[0]=index
  for i,widgets in paint:
   active=i==index
   for w in widgets:
    if isinstance(w,(tk.Frame,tk.Label,tk.Entry)):
     w.configure(bg=WHITE if active else (ROW if i%2==0 else ALT))
     if isinstance(w,(tk.Label,tk.Entry)):w.configure(fg=INK if active else TEXT)
 def bulk(group):
  c.bulk(group)
  for f in (c.data or {'fields':[]})['fields']:
   if f['group']==group and f['id'] in variables:variables[f['id']].set(c.values[f['id']])
 def draw_fields():
  variables.clear();paint.clear();chosen[0]=None
  for key in ('Player','Attributes','Badges'):canvases.pop(key,None)
  for group in ('Player','Attributes','Badges'):
   parent=pages[group]
   for w in parent.winfo_children():w.destroy()
   banner=tk.Frame(parent,bg=BG);banner.pack(fill='x',pady=10)
   tk.Label(banner,text=c.data['name'].upper(),bg=BG,fg=TEXT,font=('DejaVu Sans',14,'bold')).pack(side='left')
   if group!='Player':button(banner,'MAX ATTRIBUTES' if group=='Attributes' else 'ALL BADGES • GOLD',lambda g=group:bulk(g),True).pack(side='right')
   hint={'Player':'Height and wingspan snap in one-inch steps  •  Arm length changes the model','Attributes':'Max attributes sets raw values to 255.','Badges':'Skill badges: Gold  •  Personality badges: On'}[group]
   tk.Label(parent,text=hint,bg=BG,fg=MUTED,anchor='w',font=('DejaVu Sans',10),wraplength=960).pack(fill='x',pady=(0,10))
   region=tk.Frame(parent,bg=BG);region.pack(fill='both',expand=True)
   canvas=tk.Canvas(region,bg=BG,highlightthickness=0);canvases[group]=canvas
   scroll=ttk.Scrollbar(region,orient='vertical',command=canvas.yview);scroll.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True);canvas.configure(yscrollcommand=scroll.set)
   content=tk.Frame(canvas,bg=BG);window=canvas.create_window(0,0,window=content,anchor='nw')
   content.bind('<Configure>',lambda _,cv=canvas:cv.configure(scrollregion=cv.bbox('all')))
   canvas.bind('<Configure>',lambda e,cv=canvas,wi=window:cv.itemconfigure(wi,width=e.width))
   for f in (f for f in c.data['fields'] if f['group']==group):
    i=f['id'];bg=ROW if i%2==0 else ALT;enabled=f.get('enabled',True)
    row=tk.Frame(content,bg=bg,height=40);row.pack(fill='x',pady=1);row.grid_columnconfigure(0,weight=1);row.grid_columnconfigure(2,weight=1,minsize=220)
    label=tk.Label(row,text=f['name'].replace('Height (inches; 84 = 7 ft)','Height'),bg=bg,fg=TEXT,anchor='w',font=('DejaVu Sans',11,'bold'));label.grid(row=0,column=0,sticky='ew',padx=12,pady=9)
    var=tk.StringVar(value=c.values[i]);variables[i]=var
    widgets=[row,label];row.bind('<Button-1>',lambda _,i=i:select_row(i));label.bind('<Button-1>',lambda _,i=i:select_row(i))
    def update(*_,i=i,v=var):c.values[i]=v.get()
    var.trace_add('write',update)
    if f.get('options'):
     choices=f['options'];keys=list(choices);view=tk.StringVar()
     def show(*_,v=var,out=view,opts=choices):
      try:out.set(opts.get(str(int(float(v.get()))),v.get()))
      except ValueError:out.set(v.get())
     var.trace_add('write',show);show()
     def step(delta,v=var,keys=keys,i=i,enabled=enabled):
      if not enabled:return
      try:k=keys.index(str(int(float(v.get()))))
      except (ValueError,TypeError):k=0
      v.set(keys[(k+delta)%len(keys)]);select_row(i)
     picker=tk.Frame(row,bg=bg);picker.grid(row=0,column=1,columnspan=2,sticky='e',padx=14)
     left=button(picker,'◀',lambda step=step:step(-1));left.pack(side='left')
     value=tk.Label(picker,textvariable=view,bg=bg,fg=TEXT,width=22,font=('DejaVu Sans',11));value.pack(side='left',padx=8)
     right=button(picker,'▶',lambda step=step:step(1));right.pack(side='left');widgets.extend([picker,value])
     if not enabled:left.configure(state='disabled');right.configure(state='disabled')
    else:
     if f.get('display')=='feet_inches':
      view=tk.StringVar()
      def display_height(*_,v=var,out=view):out.set(format_height(v.get()))
      var.trace_add('write',display_height);display_height()
      entry=tk.Label(row,textvariable=view,width=9,bg=bg,fg=TEXT,font=('DejaVu Sans',11,'bold'))
      entry.grid(row=0,column=1,padx=8);widgets.append(entry)
     else:
      entry=tk.Entry(row,textvariable=var,width=9,bg=bg,fg=TEXT,insertbackground=YELLOW,relief='flat',justify='center',font=('DejaVu Sans',11,'bold'),highlightthickness=0)
      entry.grid(row=0,column=1,padx=8);entry.bind('<FocusIn>',lambda _,i=i:select_row(i));widgets.append(entry)
     lo=f.get('min',0);hi=f.get('max',(1<<f['bits'])-1);step=f.get('step',1)
     slider=tk.Canvas(row,height=30,width=230,bg=bg,highlightthickness=0,cursor='hand2');slider.grid(row=0,column=2,sticky='ew',padx=(5,14))
     def render(*_,cv=slider,v=var,lo=lo,hi=hi):
      cv.delete('all');width=max(40,cv.winfo_width());start=8;end=width-8
      try:fraction=max(0,min(1,(float(v.get())-lo)/(hi-lo)))
      except ValueError:fraction=0
      pos=start+(end-start)*fraction
      cv.create_rectangle(start,13,end,17,fill='#050606',outline='#4d504d')
      cv.create_rectangle(start,13,pos,17,fill=YELLOW,outline='')
      cv.create_rectangle(pos-2,9,pos+2,21,fill=WHITE,outline='')
     def slide(event,v=var,cv=slider,lo=lo,hi=hi,step=step,i=i,enabled=enabled):
      if not enabled:return
      fraction=max(0,min(1,(event.x-8)/max(1,cv.winfo_width()-16)))
      number=max(lo,min(hi,round(round(fraction*(hi-lo)/step)*step+lo,4)))
      v.set(str(number));select_row(i)
     def nudge(delta,v=var,lo=lo,hi=hi,step=step,enabled=enabled):
      if enabled:v.set(str(max(lo,min(hi,round(float(v.get())/step+delta)*step))))
     slider.configure(takefocus=1)
     slider.bind('<Left>',lambda _,fn=nudge:fn(-1));slider.bind('<Right>',lambda _,fn=nudge:fn(1))
     slider.bind('<Configure>',render);slider.bind('<Button-1>',slide);slider.bind('<B1-Motion>',slide);var.trace_add('write',render)
     if not enabled:entry.configure(state='disabled')
    paint.append((i,widgets))
 def wheel(event):
  current=notebook.select()
  for group,canvas in canvases.items():
   if str(pages[group])==current:canvas.yview_scroll(-1 if event.num==4 or getattr(event,'delta',0)>0 else 1,'units')
 root.bind_all('<Button-4>',wheel);root.bind_all('<Button-5>',wheel);root.bind_all('<MouseWheel>',wheel)
 last_rows=None;last_data=None
 def close():
  if c.close():root.destroy()
 root.protocol('WM_DELETE_WINDOW',close)
 def tick():
  nonlocal last_rows,last_data
  c.poll();status.set(c.status)
  if c.rows is not last_rows:
   tree.delete(*tree.get_children())
   for r in c.rows:tree.insert('','end',iid=str(r['pid']),values=(r['pid'],r['name'],r['comm']))
   if c.selected is not None and tree.exists(str(c.selected)):tree.selection_set(str(c.selected))
   last_rows=c.rows
  if c.data is not last_data:
   if c.data:
    draw_fields()
    if last_data is None:notebook.select(pages['Player'])
   else:
    for group in ('Player','Attributes','Badges'):
     for widget in pages[group].winfo_children():widget.destroy()
   last_data=c.data
  if c.closing and not c.busy:close();return
  root.after(100,tick)
 tick();root.mainloop()
