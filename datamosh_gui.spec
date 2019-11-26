# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['datamosh_gui.py'],
             pathex=['/media/jr/Mnemonic Courier/source/py/datamosh'],
             binaries=[],
             datas=[('venv/lib/python3.6/site-packages/yaspin/data/spinners.json', 'yaspin/data'), ('empty.txt', 'spinners')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='datamosh_gui',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
