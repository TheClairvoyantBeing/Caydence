# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

a = Analysis(
    ['caydence_entry.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config', 'config'),
    ],
    hiddenimports=[
        'caydence',
        'modules.audio_engine',
        'modules.voice_engine',
        'modules.sound_design',
        'modules.spatial_mix',
        'modules.cue_sheet',
        'modules.story_engine',
        'modules.utils',
        'modules.pipeline',
        'modules.pipeline.catalog',
        'modules.pipeline.orchestrator',
        'modules.pipeline.scriptwriter',
        'modules.pipeline.synthesizer',
        'edge_tts',
        'pyloudnorm',
        'soundfile',
        'soxr',
        'yaml',
        'pydub',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'torchaudio'],
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
    name='caydence-windows-x64',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
