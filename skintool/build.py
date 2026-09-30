# -*- coding: utf-8 -*-
# CLI: skins\<Герой>.png -> общий пак. build.bat / build.py [--game] [--no-install] [--restore] [--paks ПУТЬ] [--list]
import os,sys,glob,json,argparse
import core
def main():
    ap=argparse.ArgumentParser(description='Java-скины -> Dungeons II')
    ap.add_argument('--match',action='store_true',help='игровые глаза с цветами из вашего скина'); ap.add_argument('--eyes',choices=['hide','game','match','shift','auto'],help='режим глаз для всех скинов (по умолчанию hide; можно задать по героям в config.json: {"eyes":{"Violet":"shift"}})'); ap.add_argument('--auto-eyes',action='store_true',help='match если нарисованные глаза на строке игровых, иначе hide'); ap.add_argument('--game',action='store_true',help='оставить анимированные глаза/рот игры (по умолчанию скрыты)')
    ap.add_argument('--no-install',action='store_true'); ap.add_argument('--restore',action='store_true')
    ap.add_argument('--paks'); ap.add_argument('--skins',default='skins'); ap.add_argument('--list',action='store_true')
    ap.add_argument('--cape',action='store_true',help='плащи из skins\\capes\\<Имя>.png (32x16)')
    A=ap.parse_args(); log=lambda *a:print(*a,flush=True)
    if A.list: log(', '.join(sorted(core.SKINS))); log('Плащи:',', '.join(sorted(core.CAPES))); return
    paks=core.find_paks(A.paks) 
    if not paks and not A.no_install: sys.exit('Не нашёл папку Paks. Укажите --paks "...\\Minecraft Dungeons II\\Dungeons\\Content\\Paks"')
    if A.restore: core.restore(paks,log); return
    here=os.path.dirname(os.path.abspath(__file__)); sdir=os.path.abspath(A.skins) if (os.path.isabs(A.skins) or os.path.isdir(A.skins)) else os.path.join(here,A.skins)
    cfgp=next((c for c in (os.path.join(sdir,'config.json'),os.path.join(here,'config.json')) if os.path.exists(c)),os.path.join(here,'config.json')); cfg=json.load(open(cfgp,encoding='utf-8-sig')) if os.path.exists(cfgp) else {}; cmap=cfg.get('map',{})
    entries=[]
    for f in sorted(glob.glob(os.path.join(sdir,'*.png'))):
        b=os.path.splitext(os.path.basename(f))[0]; h=cmap.get(os.path.basename(f),cmap.get(b,b))
        k=next((k for k in core.SKINS if k.lower()==h.lower()),None)
        if not k: log(f'ПРОПУСК {os.path.basename(f)}: нет героя "{h}" (--list)'); continue
        gm='auto' if A.auto_eyes else 'match' if A.match else 'game' if A.game else 'hide'
        eyes=A.eyes or cfg.get('eyes',{}).get(k,cfg.get('eyes',{}).get(b,gm))
        entries.append({'file':f,'hero':k,'arms':'auto','eyes':eyes})
    capes=[]
    if A.cape:
        for f in glob.glob(os.path.join(sdir,'capes','*.png')):
            b=os.path.splitext(os.path.basename(f))[0]; k=next((k for k in core.CAPES if k.lower()==b.lower()),None)
            if k: capes.append((f,k))
    if not entries and not capes: sys.exit('В skins\\ нет PNG с подходящими именами.')
    outdir=os.path.join(core.data_dir(),'out'); files=core.build_pack(entries,outdir,capes,log)
    if not A.no_install: core.install(files,paks,log)
main()
