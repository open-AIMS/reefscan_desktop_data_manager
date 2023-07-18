# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['src\\main.py'],
    pathex=['src','real_src'],
    binaries=[('venv\\Lib\\site-packages\\tensorflow\\python\\_pywrap*.pyd', '.')],
    datas=[('src\\resources\\*', 'resources'), ('venv\\Lib\\site-packages\\tensorflow', 'tensorflow'), ('venv\\Lib\\site-packages\\tensorflow_estimator', 'tensorflow_estimator'), ('venv\\Lib\\site-packages\\keras', 'keras'), ('venv\\Lib\\site-packages\\keras_preprocessing', 'keras_preprocessing'), ('venv\\Lib\\site-packages\\inferencer\\models', 'inferencer\\models')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='reefscan-transom-installer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['src\\resources\\aims_fish.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='reefscan-transom-installer',
)
