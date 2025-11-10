# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'markdown',
        'watchdog',
    ],
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
    [],
    exclude_binaries=True,
    name='SiText',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disabled for better compatibility
    console=False,  # GUI app, no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',  # Build for Apple Silicon (M1/M2/M3)
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # Disabled for ARM64 compatibility
    upx_exclude=[],
    name='SiText',
)

app = BUNDLE(
    coll,
    name='SiText.app',
    icon='images/icon_rounded.icns',
    bundle_identifier='com.silasslack.sitext',
    version='0.1.0',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'LSBackgroundOnly': 'False',
        'LSUIElement': 'False',
        'CFBundleShortVersionString': '0.1.0',
        'CFBundleVersion': '0.1.0',
        'CFBundleName': 'SiText',
        'CFBundleDisplayName': 'SiText',
        'CFBundleExecutable': 'MacOS/SiText',
        'NSAppleScriptEnabled': 'False',
        'LSApplicationCategoryType': 'public.app-category.productivity',
    },
)
