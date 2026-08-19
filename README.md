# 3DE Electrical Utility v5

A Windows utility for post-processing DXF electrical logical schematics exported from CATIA 3DEXPERIENCE.

The project was created as an engineering automation experiment with the assistance of ChatGPT.  
The utility itself works locally and does **not** require ChatGPT or an Internet connection to process DXF files.

## What it does

From one source DXF, the utility can generate:

- **Processed DXF** — electrical-line blocks are assigned to layers named from the text inside the blocks; line geometry is changed from explicit `Color 255` to `ByLayer`; text is normalized to Arial.
- **CSV report** — mapping between the original `BLOCKxx`, electrical-line designation, generated layer, and geometry type.
- **Interactive HTML/SVG** — search, highlighting, click-to-select, pan/zoom, mobile pinch-to-zoom, and zoom buttons.
- **Searchable PDF** — vector PDF with PDF layers (Optional Content Groups) and searchable text, including Cyrillic text when Arial is available.

## DXF export settings in 3DEXPERIENCE

The current recognition algorithm was developed and tested using the following DXF2D export settings:

- Format: **DXF**
- Version: **DXF/DWG 2010**
- Export sheets: **All**
- Export mode: **Semantic**
- Dimensions: **As Dimensions**
- Blocks: **One Level**
- Export layer number: **Enabled**

The exact naming of options may differ depending on the 3DEXPERIENCE release / localization.

## Recognition logic

The utility does **not** depend on random block names such as `BLOCK29` or `BLOCK70`.

For the tested 3DEXPERIENCE export, an electrical line is identified by its block structure:

- one `POLYLINE`, `LWPOLYLINE`, or `LINE`;
- two identical text labels inside the block.

The repeated text is treated as the electrical-line designation and is used as the generated layer name.

> Important: before production use, test the algorithm on multiple schematics from your own environment. DXF structure may vary between projects, templates, and software releases.

## Requirements for building

- Windows 10/11 x64
- Python 3.11 x64 recommended
- Dependencies:
  - `ezdxf`
  - `PyMuPDF`
  - `PyInstaller` (build only)

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Build the Windows EXE

The easiest method on Windows:

```text
BUILD_EXE_FIXED_V3.bat
```

The build script creates a virtual environment, installs dependencies, and builds:

```text
dist\3DE_Electrical_Utility_v5.exe
```

After the EXE is built, end users do not need Python installed.

## Usage

1. Export the electrical logical schematic from 3DEXPERIENCE to DXF.
2. Start `3DE_Electrical_Utility_v5.exe`.
3. Add one or more DXF files.
4. Choose the required outputs.
5. Click **Process / ОБРАБОТАТЬ**.
6. Open the generated files from the output directory.

The source DXF is not overwritten.

## Output files

For a source file named:

```text
scheme.dxf
```

the utility can generate:

```text
scheme_layers_Arial.dxf
scheme_mapping.csv
scheme_interactive.html
scheme_layers_searchable.pdf
```

## Tested prototype

On the initial test schematic, the prototype recognized:

- 125 electrical-line blocks;
- 556 text objects converted to Arial;
- PDF layers created from the processed DXF;
- searchable Latin and Cyrillic line designations.

These values describe the original test case only and are **not** hard-coded requirements.

## Project status

**Experimental / prototype.**

The utility is currently intended for testing on additional electrical schematics exported from 3DEXPERIENCE.  
Before using generated files in a production workflow, verify the result against the source schematic.

## Binary release

Prebuilt Windows binaries should be distributed through the **GitHub Releases** section rather than committed directly into the source repository.

## Development

The project was developed iteratively with ChatGPT:

1. analysis of a real exported DXF;
2. automatic creation of DXF layers from block text;
3. normalization of colors and fonts;
4. interactive HTML/SVG viewer;
5. desktop and mobile interaction improvements;
6. vector PDF generation with layers and searchable text;
7. packaging as a Windows utility.

This project is an example of using modern AI-assisted coding for small engineering automation tasks.

## Disclaimer

This is an independent experimental project and is not an official Dassault Systèmes product.

CATIA and 3DEXPERIENCE are trademarks or registered trademarks of their respective owners.

## License

No open-source license is included yet.

Before allowing third parties to freely reuse, modify, or redistribute the source code, choose and add an appropriate license (for example MIT, Apache-2.0, or another license that fits your intended use).
