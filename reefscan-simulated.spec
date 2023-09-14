# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['src\\main.py'],
    pathex=['src', 'simulated_src'],
    binaries=[('venv\\Lib\\site-packages\\tensorflow\\python\\_pywrap*.pyd', '.')],
    datas=[('src\\resources\\*', 'resources'), ('venv\\Lib\\site-packages\\tensorflow', 'tensorflow'), ('venv\\Lib\\site-packages\\tensorflow_estimator', 'tensorflow_estimator'), ('venv\\Lib\\site-packages\\keras', 'keras'), ('venv\\Lib\\site-packages\\keras_preprocessing', 'keras_preprocessing'), ('venv\\Lib\\site-packages\\inferencer\\models', 'inferencer\\models'), ('src\\fake_data\\camera\\a\\*', 'fake_data\\camera\\a'), ('src\\fake_data\\camera\\b\\*', 'fake_data\\camera\\b'), ('src\\fake_data\\local\\a\\*', 'fake_data\\local\\a'), ('src\\fake_data\\local\\b\\*', 'fake_data\\local\\b'), ('src\\fake_data\\local\\c\\*', 'fake_data\\local\\c'), ('src\\fake_data\\camera\\archive\\a\\*', 'fake_data\\camera\\archive\\a'), ('src\\fake_data\\camera\\archive\\b\\*', 'fake_data\\camera\\archive\\b')],
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
    name='reefscan-simulated',
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
