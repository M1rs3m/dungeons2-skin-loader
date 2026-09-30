#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Достаёт из ВАШЕЙ копии Minecraft Dungeons II всё, что нужно конвертеру, и кладёт в skintool/base и skintool/mesh.
Extracts from YOUR OWN copy of Minecraft Dungeons II everything the converter needs into skintool/base and skintool/mesh.

  python tools/extract_from_game.py --aes 0xXXXXXXXX...   [--paks "...\\Dungeons\\Content\\Paks"]

Ключ AES можно передать через --aes, переменную окружения MD2_AES_KEY или ввести по запросу. В репозиторий он не попадает.
Результат (base/, mesh/, retoc/) - ваши локальные файлы, игровые данные; не публикуйте их (они в .gitignore).
"""
import os, sys, re, glob, shutil, struct, hashlib, zipfile, argparse, subprocess, tempfile, urllib.request
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOL = os.path.join(ROOT, 'skintool')

RETOC_URL = 'https://github.com/trumank/retoc/releases/download/v0.1.5/retoc_cli-x86_64-pc-windows-msvc.zip'
RETOC_SHA256 = 'cc036b06ad3bdcf7003690b00d82719980c374e48a95bf0654f9959148d263aa'

# смещения внутри SK_Player_Master.uexp (UE5.6, версия игры на момент написания) / offsets inside SK_Player_Master.uexp
N_VERT, N_IDX = 608, 2310
OFF_IB, OFF_P, OFF_UV = 3871, 8507, 20701

def log(*a): print(*a, flush=True)

def steam_libraries():
    libs = []
    try:
        import winreg
        for hive, key in ((winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam'), (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam')):
            try:
                k = winreg.OpenKey(hive, key)
                for name in ('SteamPath', 'InstallPath'):
                    try: libs.append(winreg.QueryValueEx(k, name)[0].replace('/', '\\'))
                    except OSError: pass
            except OSError: pass
    except ImportError: pass
    for l in list(libs):
        vdf = os.path.join(l, 'steamapps', 'libraryfolders.vdf')
        if os.path.exists(vdf):
            for m in re.finditer(r'"path"\s+"([^"]+)"', open(vdf, encoding='utf-8', errors='ignore').read()):
                libs.append(m.group(1).replace('\\\\', '\\'))
    for d in 'CDEFGH':
        libs += [d + ':\\SteamLibrary', d + ':\\Program Files (x86)\\Steam', d + ':\\Steam', d + ':\\Games\\Steam']
    return list(dict.fromkeys(libs))

def find_paks(hint):
    cands = [hint] if hint else [os.path.join(l, 'steamapps', 'common', 'Minecraft Dungeons II', 'Dungeons', 'Content', 'Paks') for l in steam_libraries()]
    for p in cands:
        if p and os.path.exists(os.path.join(p, 'Dungeons-Windows.utoc')): return p
    sys.exit('Не нашёл папку Paks. Укажите --paks / Paks folder not found, use --paks "...\\Minecraft Dungeons II\\Dungeons\\Content\\Paks"')

def ensure_retoc():
    exe = os.path.join(TOOL, 'retoc', 'retoc.exe')
    if os.path.exists(exe): return exe
    os.makedirs(os.path.dirname(exe), exist_ok=True)
    log('Скачиваю retoc v0.1.5 (github.com/trumank/retoc, MIT) ...')
    tmp = os.path.join(tempfile.gettempdir(), 'retoc_cli.zip')
    urllib.request.urlretrieve(RETOC_URL, tmp)
    h = hashlib.sha256(open(tmp, 'rb').read()).hexdigest()
    if h != RETOC_SHA256: sys.exit(f'SHA-256 retoc не совпал ({h}) - остановлено / checksum mismatch')
    with zipfile.ZipFile(tmp) as z:
        m = next(n for n in z.namelist() if n.lower().endswith('retoc.exe'))
        open(exe, 'wb').write(z.read(m))
    return exe

def run_retoc(exe, key, paks, out, filt):
    cmd = [exe, '-a', key, 'to-legacy', '--version', 'UE5_6', '--no-shaders', '--no-script-objects', '--filter', filt, paks, out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    txt = (r.stdout + r.stderr).replace(key, '<KEY>')
    if r.returncode != 0: sys.exit('retoc завершился с ошибкой:\n' + txt[-1500:])
    log('  ', filt, '->', (txt.strip().splitlines() or [''])[-1])

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--aes'); ap.add_argument('--paks'); ap.add_argument('--keep', action='store_true', help='не удалять временную папку'); ap.add_argument('--ignore-pack', action='store_true', help=argparse.SUPPRESS)
    A = ap.parse_args()
    key = A.aes or os.environ.get('MD2_AES_KEY') or input('AES-ключ (0x...): ').strip()
    if not re.fullmatch(r'(0x)?[0-9A-Fa-f]{64}', key): sys.exit('AES-ключ: ожидается 64 hex-символа (32 байта), можно с 0x')
    if not key.startswith('0x'): key = '0x' + key
    paks = find_paks(A.paks)
    mine = [f for f in glob.glob(os.path.join(paks, 'Dungeons-ZZZ_Skins_P.*'))]
    if mine and not A.ignore_pack:
        sys.exit('В Paks установлен пак скинов (Dungeons-ZZZ_Skins_P.*): он перекрывает оригинальные текстуры, и они были бы извлечены изменёнными.\n'
                 'Сначала откатите (skintool\\restore.bat / удалите эти 3 файла), запустите извлечение, затем ставьте скины заново.\n'
                 'A skin pack is installed in Paks and would override the original textures. Run restore first, extract, then reinstall.')
    exe = ensure_retoc()
    tmp = os.path.join(TOOL, 'skintool_data', 'extract'); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    log('Распаковка ассетов из', paks)
    for f in ('Player/Skins/', 'Player/Capes/Skins/', 'Player/Master/SK_Player_Master'):
        run_retoc(exe, key, paks, tmp, f)

    pat = re.compile(r'^T_[A-Za-z]+_Skin(_PreOrder|_Deluxe)?$|^T_[A-Za-z]+Cape$')
    want = {os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(tmp, '**', '*.uasset'), recursive=True)}
    want = {n for n in want if pat.match(n)}
    base = os.path.join(TOOL, 'base'); os.makedirs(base, exist_ok=True); found = {}
    for p in glob.glob(os.path.join(tmp, '**', '*.uasset'), recursive=True):
        n = os.path.splitext(os.path.basename(p))[0]
        if n in want and os.path.exists(p[:-7] + '.uexp'):
            shutil.copy(p, base); shutil.copy(p[:-7] + '.uexp', base); found[n] = 1
    miss = sorted(want - set(found))
    log(f'base/: {len(found)} текстур из {len(want)}' + (f'  НЕ НАЙДЕНО: {", ".join(miss)}' if miss else ''))

    sk = next(iter(glob.glob(os.path.join(tmp, '**', 'SK_Player_Master.uexp'), recursive=True)), None)
    if not sk: sys.exit('SK_Player_Master.uexp не найден')
    d = open(sk, 'rb').read()
    IB = np.frombuffer(d, '<u2', N_IDX, OFF_IB).reshape(-1, 3).copy()
    P = np.frombuffer(d, '<f4', N_VERT * 3, OFF_P).reshape(-1, 3).copy()
    UV = np.frombuffer(d, '<f2', N_VERT * 2, OFF_UV).astype(np.float64).reshape(-1, 2) * 64
    ok = IB.max() < N_VERT and np.isfinite(P).all() and np.isfinite(UV).all() and 0 <= UV.min() and UV.max() <= 64 and abs(P).max() < 500
    if not ok:
        sys.exit('Меш не прошёл проверку: смещения в SK_Player_Master.uexp не совпали с этой версией игры. '
                 'Откройте issue и приложите размер файла (' + str(len(d)) + ' байт).')
    mesh = os.path.join(TOOL, 'mesh'); os.makedirs(mesh, exist_ok=True)
    np.save(os.path.join(mesh, 'P.npy'), P); np.save(os.path.join(mesh, 'UV.npy'), UV); np.save(os.path.join(mesh, 'IB.npy'), IB)
    log(f'mesh/: P{P.shape} UV{UV.shape} IB{IB.shape} - OK')
    if not A.keep: shutil.rmtree(tmp, ignore_errors=True)
    log('Готово. Дальше: python skintool/build.py  (или skintool/run.bat)')

if __name__ == '__main__': main()
