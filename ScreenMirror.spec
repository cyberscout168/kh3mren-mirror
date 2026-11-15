# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['screenmirror/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('platform-tools(Windows)', 'platform-tools(Windows)'),
        ('third_party/scrcpy', 'third_party/scrcpy'),
        ('assets/screenmirror.ico', 'assets'),
        ('assets/screenmirror.png', 'assets'),
    ],
    hiddenimports=[],
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
    icon='assets/screenmirror.ico',
    exclude_binaries=True,
    name='ScreenMirror',
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
    name='ScreenMirror',
)
