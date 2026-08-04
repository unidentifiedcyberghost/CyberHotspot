# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('cyberhotspot\\assets', 'cyberhotspot\\assets')]
binaries = []
hiddenimports = ['winrt.system', 'winrt.windows.foundation', 'winrt.windows.networking.connectivity', 'winrt.windows.networking.networkoperators']
tmp_ret = collect_all('winrt.windows.foundation')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('winrt.windows.networking.connectivity')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('winrt.windows.networking.networkoperators')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['cyberhotspot\\gui.py'],
    pathex=['C:\\Users\\MSI\\Desktop\\Project-WhiteHatDevTools\\CyberHotspot-v2.8.0-Local-Observability-HUD\\CyberHotspot'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CyberHotspot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CyberHotspot',
)
