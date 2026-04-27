# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

# Inclui assets do customtkinter (temas, fontes, imagens)
datas = collect_data_files("customtkinter")

# Inclui schemas XSD e notas técnicas
datas += [("docs", "docs")]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=["customtkinter"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="ConferenciaXMLIBSCBS",
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    icon="icon.ico",
)
