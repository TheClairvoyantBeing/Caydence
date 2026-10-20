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
        'caydence.audio_engine',
        'caydence.voice_engine',
        'caydence.sound_design',
        'caydence.spatial_mix',
        'caydence.cue_sheet',
        'caydence.story_engine',
        'caydence.utils',
        'caydence.pipeline',
        'caydence.pipeline.catalog',
        'caydence.pipeline.orchestrator',
        'caydence.pipeline.scriptwriter',
        'caydence.pipeline.synthesizer',
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
