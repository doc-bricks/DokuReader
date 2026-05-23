# -*- mode: python ; coding: utf-8 -*-

datas = [
    ('locales', 'locales'),
    ('DokuReader.ico', '.'),
]
binaries = []
hiddenimports = [
    '_tkinter',
    'PIL._tkinter_finder',
    'PIL.Image',
    'PIL.ImageTk',
]


a = Analysis(
    ['DokuReader.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'IPython',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'cv2',
        'matplotlib',
        'numpy',
        'pandas',
        'pytest',
        'scipy',
        'torch',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DokuReader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['DokuReader.ico'],
)
