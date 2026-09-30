# -*- coding: utf-8 -*-
"""skintool core: Java-скины -> Minecraft Dungeons II. Используется и build.py (CLI), и gui.py."""
import os,sys,re,json,shutil,struct,subprocess,glob,base64,urllib.request
import numpy as np
from PIL import Image
def res_dir():   # где лежат base/, mesh/, retoc/ (внутри exe - во временной папке PyInstaller)
    return getattr(sys,'_MEIPASS',os.path.dirname(os.path.abspath(__file__)))
def data_dir():  # куда писать work/out/кэш: рядом с exe/скриптом, иначе LOCALAPPDATA
    base=os.path.dirname(sys.executable) if getattr(sys,'frozen',False) else os.path.dirname(os.path.abspath(__file__))
    d=os.path.join(base,'skintool_data')
    try: os.makedirs(d,exist_ok=True); open(os.path.join(d,'.w'),'w').close(); return d
    except Exception:
        d=os.path.join(os.environ.get('LOCALAPPDATA',os.path.expanduser('~')),'skintool'); os.makedirs(d,exist_ok=True); return d
RES=res_dir(); sys.path.insert(0,RES)
import convlib
SK='Dungeons/Content/Spicewood/Art/Characters/Player/Skins/'
CP='Dungeons/Content/Spicewood/Art/Characters/Player/Capes/Skins/'
SKINS={'Alex':('Alex','T_Alex_Skin_PreOrder'),'Steve':('Steve','T_Steve_Skin_PreOrder'),
 'Darian':('Darian','T_Darian_Skin'),'Eshe':('Eshe','T_Eshe_Skin'),'Esperanza':('Esperanza','T_Esperanza_Skin'),
 'Greta':('Greta','T_Greta_Skin'),'Healer':('Healer','T_Healer_Skin'),'Healer_Deluxe':('Healer','T_Healer_Skin_Deluxe'),
 'Javier':('Javier','T_Javier_Skin'),'Nuru':('Nuru','T_Nuru_Skin'),'PizzaChef':('PizzaChef','T_PizzaChef_Skin'),
 'Qamar':('Qamar','T_Qamar_Skin'),'Ranger':('Ranger','T_Ranger_Skin'),'Ranger_Deluxe':('Ranger','T_Ranger_Skin_Deluxe'),
 'Tank':('Tank','T_Tank_Skin'),'Tank_Deluxe':('Tank','T_Tank_Skin_Deluxe'),'Valorie':('Valorie','T_Valorie_Skin'),
 'Valorie_Deluxe':('Valorie','T_Valorie_Skin_Deluxe'),'Violet':('Violet','T_Violet_Skin')}
for _c in ('Brown','Gray','Green','Mint','Pink','Plum','Purple','Silver','Yellow'): SKINS[_c]=('_'+_c,f'T_{_c}_Skin')
CAPES={c:(c+'Cape',f'T_{c}Cape') for c in ('CorruptedCreeper','Hero','Mojang','SliceSlayer','Soul','Special','Twisted')}
PACK='Dungeons-ZZZ_Skins_P'; OLD=['Dungeons-ZZZ_TestSkin_P']
EXTS=('utoc','ucas','pak')
def _noop(*a): pass
# ---------- поиск игры ----------
def steam_libraries():
    libs=[]
    try:
        import winreg
        for hive,key in ((winreg.HKEY_CURRENT_USER,r'Software\Valve\Steam'),(winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\WOW6432Node\Valve\Steam')):
            try:
                k=winreg.OpenKey(hive,key)
                for name in ('SteamPath','InstallPath'):
                    try: libs.append(winreg.QueryValueEx(k,name)[0].replace('/','\\'))
                    except OSError: pass
            except OSError: pass
    except ImportError: pass
    for l in list(libs):
        vdf=os.path.join(l,'steamapps','libraryfolders.vdf')
        if os.path.exists(vdf):
            try:
                for m in re.finditer(r'"path"\s+"([^"]+)"',open(vdf,encoding='utf-8',errors='ignore').read()): libs.append(m.group(1).replace('\\\\','\\'))
            except Exception: pass
    for d in 'CDEFGH':
        libs+= [d+':\\SteamLibrary',d+':\\Program Files (x86)\\Steam',d+':\\Steam',d+':\\Games\\Steam']
    return list(dict.fromkeys(libs))
def find_paks(hint=None):
    cands=[hint] if hint else []
    cands+=[os.path.join(l,'steamapps','common','Minecraft Dungeons II','Dungeons','Content','Paks') for l in steam_libraries()]
    for p in cands:
        if p and os.path.exists(os.path.join(p,'Dungeons-Windows.utoc')): return p
    return None
def game_running():
    try: out=subprocess.run(['tasklist'],capture_output=True,text=True,creationflags=0x08000000).stdout
    except Exception: return False
    return 'Dungeons-Win64-Shipping' in out
# ---------- Mojang ----------
def _get(u):
    return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'skintool/1.0'}),timeout=20).read()
def fetch_mojang(nick,dest_dir,log=_noop):
    import json as _j
    for v in dict.fromkeys([nick,nick.lower(),nick.upper(),nick.capitalize()]):
        try: r=_j.loads(_get(f'https://api.mojang.com/users/profiles/minecraft/{v}')); break
        except Exception: r=None
    if not r: raise RuntimeError(f'Ник "{nick}" не найден в Mojang (или нет интернета)')
    p=_j.loads(_get(f"https://sessionserver.mojang.com/session/minecraft/profile/{r['id']}"))
    tex=_j.loads(base64.b64decode(p['properties'][0]['value']))['textures']
    if 'SKIN' not in tex: raise RuntimeError('у ника нет скина')
    sk=tex['SKIN']; model=sk.get('metadata',{}).get('model','classic')
    os.makedirs(dest_dir,exist_ok=True); path=os.path.join(dest_dir,f"{r['name']}_{model}.png")
    open(path,'wb').write(_get(sk['url'])); log(f"скачан {r['name']} ({model})"); return path,model
# ---------- конвертация ----------
def legacy_to_64(im):
    if im.size==(64,64): return im
    if im.size!=(64,32): raise ValueError(f'неверный размер {im.size}: нужен 64x64 (или 64x32)')
    o=Image.new('RGBA',(64,64),(0,0,0,0)); o.paste(im,(0,0))
    def mb(src,dst,w,h,d):
        (sx,sy),(dx,dy)=src,dst
        def cp(rx,ry,rw,rh,tx,ty): o.paste(im.crop((rx,ry,rx+rw,ry+rh)).transpose(Image.FLIP_LEFT_RIGHT),(tx,ty))
        cp(sx+d,sy,w,d,dx+d,dy); cp(sx+d+w,sy,w,d,dx+d+w,dy); cp(sx+d,sy+d,w,h,dx+d,dy+d); cp(sx+2*d+w,sy+d,w,h,dx+2*d+w,dy+d)
        cp(sx,sy+d,d,h,dx+d+w,dy+d); cp(sx+d+w,sy+d,d,h,dx,dy+d)
    mb((0,16),(16,48),4,12,4); mb((40,16),(32,48),4,12,4); return o
def detect_slim(im):
    a=np.array(im)[...,3]; return bool((a[20:32,54:56]==0).all() and (a[52:64,46:48]==0).all())
def read_uexp(path,w,h):
    e=bytearray(open(path,'rb').read()); foot=struct.pack('<iii',w,h,1)
    ps=[i for i in range(len(e)-12) if e[i:i+12]==foot]; return e,ps[-1]-w*h*4
def write_tex(e,s,rgba):
    a=np.array(rgba.convert('RGBA')); e[s:s+a.size]=a[...,[2,1,0,3]].tobytes()
def _lum(c): return 0.3*c[0]+0.59*c[1]+0.11*c[2]
EYE_COLS=(1,2,5,6)      # столбцы глаз на лице 8x8 (у игровых кусочков глаз: 1,2 = правый глаз персонажа, 5,6 = левый)
GAME_ROW=4              # строка лица 0..7, на которой стоят игровые глаза (y=12 в атласе)
def _face(im): return np.array(im.convert('RGBA')).astype(float)[8:16,8:16,:3]
def eye_row(im):
    """Строка лица (0..7), где нарисованы глаза Java-скина, или None. Игровая строка = 4 (y=12).
    1) строка, где >=2 столбца глаз заметно СВЕТЛЕЕ кожи между глазами (белок); 2) иначе строка, где >=3 столбца глаз заметно ТЕМНЕЕ."""
    f=_face(im); best=None
    for r in (3,4,5,6):
        s=_lum((f[r,3]+f[r,4])/2); n=sum(_lum(f[r,c])>s+45 for c in EYE_COLS)
        if n>=2 and (best is None or n>best[0]): best=(n,r)
    if best: return best[1]
    for r in (3,4,5,6):
        s=_lum((f[r,3]+f[r,4])/2); n=sum(_lum(f[r,c])<s-60 for c in EYE_COLS)
        if n>=3 and (best is None or n>best[0]): best=(n,r)
    return best[1] if best else None
def eyes_on_game_row(im): return eye_row(im)==GAME_ROW
def shift_eyes(im):
    """Сдвигает нарисованные глаза (и рот) Java-скина на 1 тексель вверх, на игровую строку y=12. Возвращает (новое RGBA-изображение, сдвинуто?).
    Работает, если глаза на строке 5 (y=13). Сдвигаются только столбцы глаз (1,2,5,6) и рта (3,4) на строках 3..7, остальное лицо не трогаем."""
    r=eye_row(im)
    if r!=GAME_ROW+1: return im,False
    a=np.array(im.convert('RGBA')); F=a[8:16,8:16].copy()
    for c in EYE_COLS:
        for k in range(r-2,r+1): F[k,c]=a[8+k+1,8+c]
    for c in (3,4):
        F[6,c]=a[8+7,8+c]; F[7,c]=a[8+7,8+(2 if c==3 else 5)]
    a[8:16,8:16]=F
    return Image.fromarray(a,'RGBA'),True
def match_eyes(out,im,row=GAME_ROW):
    """Игровые глаза/брови/рот - плоские кусочки меша (кости J_*EyeIris/EyePupil/Eyebrow/Mouth), каждый берёт цвет из ОДНОГО texel атласа.
    Соответствие проверено маркерными цветами в игре (вид спереди, лево/право - от зрителя):
      левый глаз:  внешний пиксель (6,6), внутренний (6,5)      <- столбцы лица 1 и 2
      правый глаз: внутренний пиксель (7,6), внешний (7,5)       <- столбцы лица 5 и 6
      брови: (3,7) внешняя левая, (4,7) внутренние; рот: (6,7),(7,7) <- столбцы лица 3 и 4.
    Цвета берём ровно с тех пикселей лица Java-скина, где нарисованы глаза (строка row), брови - строка row-1, рот - row+2."""
    f=_face(im)
    put=lambda x,y,c: out.__setitem__((y,x),[int(round(c[0])),int(round(c[1])),int(round(c[2])),255])
    put(6,6,f[row,1]); put(6,5,f[row,2]); put(7,6,f[row,5]); put(7,5,f[row,6])
    put(3,7,f[row-1,1]); put(4,7,(f[row-1,2]+f[row-1,5])/2)
    mr=min(row+2,7); put(6,7,f[mr,3]); put(7,7,f[mr,4])
def convert_one(png,hero,arms='auto',eyes='hide',log=_noop):
    """возвращает (RGBA ndarray 64x64, slim, базовое имя .uexp)"""
    d,t=SKINS[hero]; im=legacy_to_64(Image.open(png).convert('RGBA'))
    slim=detect_slim(im) if arms=='auto' else (arms=='slim')
    e,s=read_uexp(os.path.join(RES,'base',t+'.uexp'),64,64)
    nat=np.frombuffer(bytes(e[s:s+16384]),dtype=np.uint8).reshape(64,64,4)[...,[2,1,0,3]].copy()
    row=eye_row(im)
    if eyes=='auto': eyes='match' if row==GAME_ROW else 'hide'
    elif eyes=='shift':
        im,ok=shift_eyes(im)
        if ok: row=GAME_ROW
        eyes='match' if (ok or row==GAME_ROW) else 'hide'
    if eyes=='blink': eyes='match'
    out,filled=convlib.convert(im,slim=slim,hide_eyes=(eyes=='hide'),native=nat)
    if eyes=='match': match_eyes(out,im,row if row is not None else GAME_ROW)
    na=nat[...,3]>0; hat=np.zeros((64,64),bool); hat[0:16,32:64]=True
    for y,x in zip(*np.where(na&(out[...,3]==0)&~hat&filled)):
        for r in range(1,8):
            ok=False
            for nx,ny in ((x-r,y),(x+r,y),(x,y-r),(x,y+r)):
                if 0<=nx<64 and 0<=ny<64 and out[ny,nx,3]>0: out[y,x]=out[ny,nx]; ok=True; break
            if ok: break
    hj=np.array(im)[0:16,32:64].copy(); hj[(hj[...,3]>0)&(hj[...,3]<255)]=0; hj[...,:3][hj[...,3]==0]=0   # шляпа 1:1 из Java
    out[0:16,32:64]=hj
    return out,slim
def build_pack(entries,outdir,capes=(),log=_noop):
    """entries: [{'file','hero','arms','eyes'}]. Собирает пак в outdir. Возвращает список файлов."""
    heroes=[e['hero'] for e in entries]
    dup=[h for h in set(heroes) if heroes.count(h)>1]
    if dup: raise ValueError('Один герой выбран несколько раз: '+', '.join(dup))
    work=os.path.join(data_dir(),'work'); pin=os.path.join(work,'patch_in'); shutil.rmtree(work,ignore_errors=True); os.makedirs(pin)
    os.makedirs(outdir,exist_ok=True)
    for e in entries:
        d,t=SKINS[e['hero']]
        out,slim=convert_one(e['file'],e['hero'],e.get('arms','auto'),e.get('eyes','hide'))
        ue,s=read_uexp(os.path.join(RES,'base',t+'.uexp'),64,64); write_tex(ue,s,Image.fromarray(out,'RGBA'))
        dst=os.path.join(pin,SK,d); os.makedirs(dst,exist_ok=True)
        open(os.path.join(dst,t+'.uexp'),'wb').write(ue); shutil.copy(os.path.join(RES,'base',t+'.uasset'),dst)
        log(f"OK  {os.path.basename(e['file'])} -> {e['hero']}  ({'slim' if slim else 'classic'}, глаза игры: {'скрыты' if e.get('eyes','hide')=='hide' else 'оставлены'})")
    for f,key in capes:
        d,t=CAPES[key]; im=Image.open(f).convert('RGBA')
        if im.size!=(32,16): log(f'ПРОПУСК плаща {f}: нужен 32x16'); continue
        ue,s=read_uexp(os.path.join(RES,'base',t+'.uexp'),32,16); write_tex(ue,s,im)
        dst=os.path.join(pin,CP,d); os.makedirs(dst,exist_ok=True)
        open(os.path.join(dst,t+'.uexp'),'wb').write(ue); shutil.copy(os.path.join(RES,'base',t+'.uasset'),dst); log('OK  плащ',key)
    for ext in EXTS:
        p=os.path.join(outdir,f'{PACK}.{ext}')
        if os.path.exists(p): os.remove(p)
    retoc=os.path.join(RES,'retoc','retoc.exe')
    if not os.path.exists(retoc): raise RuntimeError('retoc.exe не найден')
    r=subprocess.run([retoc,'to-zen','--version','UE5_6',pin,os.path.join(outdir,PACK+'.utoc')],capture_output=True,text=True,creationflags=0x08000000)
    if r.returncode!=0 or not os.path.exists(os.path.join(outdir,PACK+'.pak')): raise RuntimeError('retoc: '+r.stdout+r.stderr)
    files=[os.path.join(outdir,f'{PACK}.{x}') for x in EXTS]
    for f in files: log('собрано',os.path.basename(f),os.path.getsize(f),'байт')
    return files
def install(files,paks,log=_noop):
    if game_running(): raise RuntimeError('Игра запущена - закройте её и повторите.')
    for b in OLD:
        for x in EXTS:
            f=os.path.join(paks,f'{b}.{x}')
            if os.path.exists(f): os.remove(f); log('удалён старый',os.path.basename(f))
    for f in files: shutil.copy(f,paks)
    log('УСТАНОВЛЕНО в',paks)
def restore(paks,log=_noop):
    if game_running(): raise RuntimeError('Игра запущена - закройте её и повторите.')
    n=0
    for b in [PACK]+OLD:
        for x in EXTS:
            f=os.path.join(paks,f'{b}.{x}')
            if os.path.exists(f): os.remove(f); n+=1; log('удалён',os.path.basename(f))
    log(f'Готово: удалено файлов {n}. Игра снова оригинальная.'); return n
