# -*- mode: python ; coding: utf-8 -*-
import sys
sys.setrecursionlimit(5000)
from kivy_deps import sdl2, glew
block_cipher = None


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pandas', 'matplotlib'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=True,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [('v', None, 'OPTION')],
    exclude_binaries=True,
    name='ATMReporter',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['std_white.ico'],
)
coll = COLLECT(
    exe,
    Tree('D:\\std_atm_reporter\\'),
    a.binaries,
    a.zipfiles,
    a.datas,
    collect_all=True,  # Add this line
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ATMReporter',
)
