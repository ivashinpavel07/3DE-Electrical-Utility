# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

ez_data, ez_bin, ez_hidden = collect_all("ezdxf")
pdf_data, pdf_bin, pdf_hidden = collect_all("pymupdf")

a = Analysis(
    ["3DE_Electrical_Utility.pyw"],
    pathex=[],
    binaries=ez_bin + pdf_bin,
    datas=ez_data + pdf_data,
    hiddenimports=ez_hidden + pdf_hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="3DE_Electrical_Utility_v5",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
