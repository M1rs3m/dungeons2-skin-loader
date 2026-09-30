# -*- coding: utf-8 -*-
import os,sys,threading,traceback
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from PIL import Image,ImageTk
import core
class App(tk.Tk):
    def __init__(s):
        super().__init__(); s.title('Dungeons II Skin Tool'); s.geometry('860x620'); s.minsize(820,560)
        s.items=[]; s.paks=core.find_paks()
        s.dl=os.path.join(core.data_dir(),'skins_dl')
        top=ttk.Frame(s,padding=8); top.pack(fill='x')
        ttk.Label(top,text='Папка Paks игры:').pack(side='left')
        s.paks_var=tk.StringVar(value=s.paks or 'НЕ НАЙДЕНА - нажмите «Обзор»'); ttk.Entry(top,textvariable=s.paks_var,width=80).pack(side='left',padx=6,fill='x',expand=True)
        ttk.Button(top,text='Обзор…',command=s.pick_paks).pack(side='left')
        add=ttk.LabelFrame(s,text='Добавить скин',padding=8); add.pack(fill='x',padx=8,pady=4)
        r1=ttk.Frame(add); r1.pack(fill='x')
        ttk.Button(r1,text='Выбрать PNG…',command=s.pick_png).pack(side='left')
        s.file_var=tk.StringVar(); ttk.Entry(r1,textvariable=s.file_var,width=46).pack(side='left',padx=6)
        ttk.Label(r1,text='или ник:').pack(side='left'); s.nick_var=tk.StringVar(); ttk.Entry(r1,textvariable=s.nick_var,width=16).pack(side='left',padx=4)
        ttk.Button(r1,text='Скачать',command=s.get_nick).pack(side='left')
        r2=ttk.Frame(add); r2.pack(fill='x',pady=6)
        ttk.Label(r2,text='Слот героя:').pack(side='left')
        s.hero_var=tk.StringVar(value='Pink'); ttk.Combobox(r2,textvariable=s.hero_var,values=sorted(core.SKINS),state='readonly',width=16).pack(side='left',padx=4)
        ttk.Label(r2,text='Руки:').pack(side='left',padx=(10,0))
        s.arms_var=tk.StringVar(value='auto'); ttk.Combobox(r2,textvariable=s.arms_var,values=['auto','slim','classic'],state='readonly',width=8).pack(side='left',padx=4)
        ttk.Label(r2,text='Глаза игры:').pack(side='left',padx=(10,0))
        s.eyes_var=tk.StringVar(value='hide'); ttk.Combobox(r2,textvariable=s.eyes_var,values=['hide','game','match','shift','auto'],state='readonly',width=8).pack(side='left',padx=4)
        ttk.Button(r2,text='Добавить в список',command=s.add_item).pack(side='left',padx=14)
        mid=ttk.Frame(s); mid.pack(fill='both',expand=True,padx=8)
        cols=('file','hero','arms','eyes'); s.tree=ttk.Treeview(mid,columns=cols,show='headings',height=7)
        for c,t,w in (('file','Скин (PNG)',420),('hero','Герой',120),('arms','Руки',70),('eyes','Глаза',70)): s.tree.heading(c,text=t); s.tree.column(c,width=w)
        s.tree.pack(side='left',fill='both',expand=True); s.tree.bind('<<TreeviewSelect>>',s.preview)
        s.pv=ttk.Label(mid,text='предпросмотр',anchor='center',width=22); s.pv.pack(side='left',padx=8)
        bt=ttk.Frame(s,padding=8); bt.pack(fill='x')
        ttk.Button(bt,text='Удалить выбранный',command=s.del_item).pack(side='left')
        ttk.Button(bt,text='Собрать и установить',command=lambda:s.run('install')).pack(side='left',padx=12)
        ttk.Button(bt,text='Только собрать (папка out)',command=lambda:s.run('build')).pack(side='left')
        ttk.Button(bt,text='Откатить (удалить пак)',command=lambda:s.run('restore')).pack(side='right')
        s.logw=tk.Text(s,height=9,state='disabled',bg='#111',fg='#ddd'); s.logw.pack(fill='both',padx=8,pady=(0,8))
        s.log('Один герой = один скин. Игру закройте перед установкой. Руки «auto» определяются по прозрачным пикселям скина.')
        if not s.paks: s.log('Папка игры не найдена автоматически - укажите Paks вручную (…\\Minecraft Dungeons II\\Dungeons\\Content\\Paks).')
    def log(s,*a):
        def w(): s.logw.config(state='normal'); s.logw.insert('end',' '.join(map(str,a))+'\n'); s.logw.see('end'); s.logw.config(state='disabled')
        s.after(0,w)
    def pick_paks(s):
        d=filedialog.askdirectory(title='Папка Paks')
        if d: s.paks_var.set(d)
    def pick_png(s):
        f=filedialog.askopenfilename(filetypes=[('PNG','*.png')])
        if f: s.file_var.set(f)
    def get_nick(s):
        n=s.nick_var.get().strip()
        if not n: return
        def job():
            try:
                p,m=core.fetch_mojang(n,s.dl,s.log); s.after(0,lambda:(s.file_var.set(p),s.arms_var.set('auto')))
            except Exception as e: s.log('ОШИБКА:',e)
        threading.Thread(target=job,daemon=True).start()
    def add_item(s):
        f=s.file_var.get().strip()
        if not os.path.exists(f): messagebox.showerror('Ошибка','Выберите PNG или скачайте по нику'); return
        h=s.hero_var.get()
        if any(i['hero']==h for i in s.items): messagebox.showerror('Ошибка',f'Слот {h} уже занят - выберите другого героя'); return
        try: im=Image.open(f); assert im.size in((64,64),(64,32))
        except Exception: messagebox.showerror('Ошибка','Нужен PNG 64x64 (или 64x32)'); return
        s.items.append({'file':f,'hero':h,'arms':s.arms_var.get(),'eyes':s.eyes_var.get()}); s.refresh()
    def del_item(s):
        for i in s.tree.selection(): s.items.pop(int(i))
        s.refresh()
    def refresh(s):
        s.tree.delete(*s.tree.get_children())
        for n,i in enumerate(s.items): s.tree.insert('','end',iid=str(n),values=(i['file'],i['hero'],i['arms'],i['eyes']))
    def preview(s,_=None):
        sel=s.tree.selection()
        if not sel: return
        i=s.items[int(sel[0])]
        try:
            out,slim=core.convert_one(i['file'],i['hero'],i['arms'],i['eyes'])
            bg=Image.new('RGBA',(64,64),(90,90,90,255)); bg.alpha_composite(Image.fromarray(out,'RGBA'))
            s.ph=ImageTk.PhotoImage(bg.resize((192,192),Image.NEAREST)); s.pv.config(image=s.ph,text='')
        except Exception as e: s.log('предпросмотр:',e)
    def run(s,mode):
        paks=s.paks_var.get().strip()
        if mode!='build':
            paks=core.find_paks(paks if os.path.isdir(paks) else None)
            if not paks: messagebox.showerror('Ошибка','Не найдена папка Paks игры'); return
        if mode!='restore' and not s.items: messagebox.showerror('Ошибка','Список скинов пуст'); return
        def job():
            try:
                if mode=='restore': core.restore(paks,s.log); return
                out=os.path.join(core.data_dir(),'out'); files=core.build_pack(s.items,out,(),s.log)
                if mode=='install': core.install(files,paks,s.log); s.log('Готово. Запустите игру -> «Все герои».')
                else: s.log('Файлы в',out)
            except Exception as e: s.log('ОШИБКА:',e); s.log(traceback.format_exc().splitlines()[-2])
        threading.Thread(target=job,daemon=True).start()
if __name__=='__main__': App().mainloop()
