# ⚡ 3DE Electrical Utility v5

> 🧩 Локальная Windows-утилита для автоматической обработки DXF электрических логических схем, экспортированных из CATIA 3DEXPERIENCE.
>
> 🇷🇺 Русская версия — ниже.  
> 🇬🇧 English version — in the second half of this README.

🎥 **Видео с демонстрацией 3DE_Electrical_Utility_v5:**  
[▶ Смотреть на YouTube](https://youtu.be/7Kb3Zk8sWzI)

---

# 🇷🇺 Русская версия

## 🚀 Что это за проект

**3DE Electrical Utility v5** — экспериментальная Windows-утилита для постобработки DXF-файлов электрических логических схем, экспортированных из **CATIA 3DEXPERIENCE**.

Идея проста: после экспорта схемы из 3DEXPERIENCE не выполнять вручную однотипную подготовку в AutoCAD, а передать DXF утилите и автоматически получить несколько готовых представлений схемы.

Один исходный DXF может быть преобразован сразу в:

- 📐 **обработанный DXF** со слоями по обозначениям электрических линий;
- 📊 **CSV** с соответствиями блоков, обозначений линий и слоёв;
- 🌐 **интерактивную HTML/SVG-схему** с поиском и подсветкой;
- 📄 **векторный PDF** со слоями и текстовым поиском.

Утилита работает **локально**. Для обработки новых DXF-файлов не требуется ни ChatGPT, ни подключение к Интернету.

---

## 🎬 Демонстрация работы

В видео показан полный процесс:

⚙️ настройка DXF-экспорта в 3DEXPERIENCE →  
📤 экспорт электрической логической схемы →  
🔎 просмотр структуры исходного DXF в AutoCAD →  
▶️ запуск **3DE_Electrical_Utility_v5** →  
📄 получение PDF со слоями →  
🌐 работа с интерактивной HTML-схемой.

🎥 **Видео:**  
[https://youtu.be/7Kb3Zk8sWzI](https://youtu.be/7Kb3Zk8sWzI)

---

## 🛠 Что делает утилита

### 📐 1. Обработанный DXF

Для распознанных электрических линий утилита:

- определяет обозначение линии по тексту внутри блока;
- создаёт слой с соответствующим названием;
- назначает блоку и его геометрии нужный слой;
- переводит геометрию электрической линии с явного `Color 255` на `ByLayer`;
- нормализует текст на **Arial** для более корректного отображения, в том числе кириллицы.

### 📊 2. CSV-отчёт

Создаётся таблица соответствий:

```text
BLOCKxx → обозначение электрической линии → созданный слой → тип геометрии
```

Это удобно для проверки результата и анализа структуры исходного DXF.

### 🌐 3. Интерактивная HTML/SVG-схема

HTML-файл открывается обычным браузером и позволяет:

- 🔎 искать электрическую линию по обозначению;
- 🎯 автоматически переходить к найденной линии;
- ✨ подсвечивать выбранную линию;
- 🖱️ выбирать линию кликом;
- ➕➖ масштабировать схему;
- ↔️ перемещаться по ней;
- 📱 использовать масштабирование жестами на мобильных устройствах.

Интернет для просмотра HTML не требуется.

### 📄 4. PDF со слоями и поиском

Утилита формирует векторный PDF, в котором:

- электрические линии представлены отдельными PDF-слоями;
- сохраняется текстовый поиск;
- поддерживается поиск обозначений с латиницей и кириллицей;
- не требуется ручная публикация PDF через AutoCAD.

---

## ⚙️ Настройки экспорта DXF в 3DEXPERIENCE

Текущий алгоритм разрабатывался и тестировался на DXF, полученном с такими параметрами **Compatibility / Совместимость → DXF2D**:

- 🔹 формат — **DXF**;
- 🔹 версия — **DXF/DWG 2010**;
- 🔹 экспорт листов — **All / Все**;
- 🔹 режим экспорта — **Semantic / Семантический**;
- 🔹 размеры — **As Dimensions / Как размеры**;
- 🔹 экспорт блоков — **One Level / Один уровень**;
- 🔹 экспорт номера слоя — **Enabled / Включён**.

> ⚠️ Названия пунктов могут немного отличаться в зависимости от версии и локализации 3DEXPERIENCE.

---

## 🔎 Как распознаётся электрическая линия

Утилита **не зависит от случайного имени блока** вроде `BLOCK29`, `BLOCK70` и т. п.

В исследованном DXF электрическая линия определяется по структуре блока:

- одна сущность `POLYLINE`, `LWPOLYLINE` или `LINE`;
- два одинаковых текстовых обозначения внутри блока.

Повторяющийся текст принимается за обозначение электрической линии и используется при создании слоя.

Это позволяет работать не с именем `BLOCKxx`, а с реальной семантикой схемы.

---

## 🖥 Как пользоваться

1. 📤 Экспортировать электрическую логическую схему из 3DEXPERIENCE в DXF.
2. ▶️ Запустить `3DE_Electrical_Utility_v5.exe`.
3. 📂 Добавить один или несколько исходных DXF-файлов.
4. ☑️ Выбрать необходимые результаты: DXF, CSV, HTML и/или PDF.
5. Нажать **«ОБРАБОТАТЬ»**.
6. 📁 Открыть сформированные файлы в выбранной папке.

Исходный DXF **не перезаписывается**.

---

## 📦 Какие файлы создаются

Для исходного файла:

```text
scheme.dxf
```

могут быть сформированы:

```text
scheme_layers_Arial.dxf
scheme_mapping.csv
scheme_interactive.html
scheme_layers_searchable.pdf
```

---

## 🧪 Тестовый пример

На исходной схеме, использованной при разработке, утилита автоматически обработала:

- ⚡ **125 электрических линий**;
- 🧩 **125 слоёв** по обозначениям линий;
- 🔤 **556 текстовых объектов** с нормализацией на Arial;
- 📄 PDF со слоями и текстовым поиском;
- 🌐 интерактивное представление схемы в HTML/SVG.

Эти числа относятся только к тестовой схеме и **не являются жёстко заданными параметрами программы**.

---

## 🤖 Как появился проект

Проект разрабатывался итерационно с помощью **ChatGPT** на реальном DXF, экспортированном из 3DEXPERIENCE.

В ходе разработки последовательно появились:

1. 🔎 анализ структуры DXF;
2. 📐 автоматическое создание слоёв по тексту внутри электрических блоков;
3. 🎨 перевод геометрии в `ByLayer` и нормализация шрифтов;
4. 🌐 интерактивный HTML/SVG-просмотрщик;
5. 🖥️📱 управление для ПК и мобильных устройств;
6. 📄 генерация векторного PDF со слоями и поиском;
7. ⚙️ отдельная Windows-утилита для пакетной обработки файлов.

ChatGPT использовался как инструмент для разработки, анализа и ускорения прототипирования. Готовая утилита после сборки работает самостоятельно.

---

## 🧰 Сборка EXE из исходников

### Требования

- Windows 10/11 x64;
- Python 3.11 x64 — рекомендуется;
- зависимости:
  - `ezdxf`;
  - `PyMuPDF`;
  - `PyInstaller` — только для сборки EXE.

Установка зависимостей:

```bash
python -m pip install -r requirements.txt
```

Самый простой вариант сборки под Windows:

```text
BUILD_EXE_FIXED_V3.bat
```

После сборки готовый файл появится здесь:

```text
dist\3DE_Electrical_Utility_v5.exe
```

Пользователю готового EXE установленный Python уже не нужен.

---

## ⚠️ Статус проекта

**Experimental / Prototype**

Сейчас утилита тестируется на дополнительных электрических схемах из 3DEXPERIENCE.

Перед использованием в производственном процессе рекомендуется обязательно сравнить сформированные файлы с исходной схемой.

Структура DXF может отличаться в зависимости от:

- версии 3DEXPERIENCE;
- шаблона схемы;
- настроек экспорта;
- особенностей конкретного проекта.

При необходимости алгоритм распознавания может быть адаптирован под другие варианты структуры DXF.

---

## 📥 Готовая Windows-версия

Готовые бинарные версии рекомендуется публиковать в разделе **GitHub Releases**, а не хранить EXE непосредственно среди исходного кода.

➡️ Для обычного использования достаточно скачать ZIP с `3DE_Electrical_Utility_v5.exe` из соответствующего Release.

---

## ℹ️ Disclaimer

Это независимый экспериментальный проект и **не официальный продукт Dassault Systèmes**.

CATIA и 3DEXPERIENCE являются товарными знаками или зарегистрированными товарными знаками их соответствующих правообладателей.

---

## 📜 Лицензия

Проект распространяется по лицензии **MIT License**.

Вы можете использовать, изменять и распространять исходный код в соответствии с условиями лицензии.

Подробнее см. файл [`LICENSE`](LICENSE).

---

# 🇬🇧 English version

## 🚀 About the project

**3DE Electrical Utility v5** is an experimental Windows utility for post-processing DXF electrical logical schematics exported from **CATIA 3DEXPERIENCE**.

The idea is simple: instead of performing repetitive post-processing manually in AutoCAD after exporting a schematic from 3DEXPERIENCE, the DXF can be passed to the utility and several ready-to-use outputs can be generated automatically.

From one source DXF, the utility can generate:

- 📐 a **processed DXF** with layers based on electrical-line designations;
- 📊 a **CSV report** mapping blocks, electrical-line names and layers;
- 🌐 an **interactive HTML/SVG schematic** with search and highlighting;
- 📄 a **vector PDF** with layers and searchable text.

The utility works **locally**. ChatGPT and an Internet connection are not required to process new DXF files.

---

## 🎬 Video demonstration

The video shows the complete workflow:

⚙️ DXF export settings in 3DEXPERIENCE →  
📤 exporting an electrical logical schematic →  
🔎 inspecting the original DXF structure in AutoCAD →  
▶️ running **3DE_Electrical_Utility_v5** →  
📄 opening the generated layered PDF →  
🌐 using the interactive HTML schematic.

🎥 **Watch the demonstration:**  
[https://youtu.be/7Kb3Zk8sWzI](https://youtu.be/7Kb3Zk8sWzI)

---

## 🛠 What the utility does

### 📐 1. Processed DXF

For recognized electrical lines, the utility:

- extracts the electrical-line designation from text inside the block;
- creates a layer with the corresponding name;
- assigns the block and its geometry to that layer;
- changes electrical-line geometry from explicit `Color 255` to `ByLayer`;
- normalizes text to **Arial** for more reliable display, including Cyrillic text.

### 📊 2. CSV report

A mapping table is generated:

```text
BLOCKxx → electrical-line designation → generated layer → geometry type
```

This is useful for validating the result and analyzing the source DXF structure.

### 🌐 3. Interactive HTML/SVG schematic

The generated HTML file can be opened in a regular web browser and supports:

- 🔎 searching for an electrical line by designation;
- 🎯 automatic navigation to the selected line;
- ✨ highlighting;
- 🖱️ click-to-select;
- ➕➖ zooming;
- ↔️ panning;
- 📱 pinch-to-zoom on mobile devices.

No Internet connection is required to view the HTML file.

### 📄 4. Searchable layered PDF

The utility generates a vector PDF where:

- electrical lines are represented by separate PDF layers;
- text remains searchable;
- both Latin and Cyrillic designations can be searched;
- manual PDF publishing through AutoCAD is not required.

---

## ⚙️ DXF export settings in 3DEXPERIENCE

The current recognition algorithm was developed and tested using DXF files exported with the following **Compatibility → DXF2D** settings:

- 🔹 format — **DXF**;
- 🔹 version — **DXF/DWG 2010**;
- 🔹 exported sheets — **All**;
- 🔹 export mode — **Semantic**;
- 🔹 dimensions — **As Dimensions**;
- 🔹 block export — **One Level**;
- 🔹 export layer number — **Enabled**.

> ⚠️ Option names may vary slightly depending on the 3DEXPERIENCE release and localization.

---

## 🔎 Electrical-line recognition logic

The utility does **not** depend on random block names such as `BLOCK29` or `BLOCK70`.

In the investigated DXF structure, an electrical line is recognized by the contents of its block:

- one `POLYLINE`, `LWPOLYLINE`, or `LINE` entity;
- two identical text labels inside the block.

The repeated text is treated as the electrical-line designation and is used when generating the layer name.

This allows the utility to work with the actual schematic semantics rather than the random `BLOCKxx` identifier.

---

## 🖥 Usage

1. 📤 Export the electrical logical schematic from 3DEXPERIENCE to DXF.
2. ▶️ Start `3DE_Electrical_Utility_v5.exe`.
3. 📂 Add one or more source DXF files.
4. ☑️ Select the required outputs: DXF, CSV, HTML and/or PDF.
5. Click **Process / ОБРАБОТАТЬ**.
6. 📁 Open the generated files from the selected output directory.

The source DXF is **not overwritten**.

---

## 📦 Generated files

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

---

## 🧪 Test case

On the original schematic used during development, the utility automatically processed:

- ⚡ **125 electrical lines**;
- 🧩 **125 generated layers** based on line designations;
- 🔤 **556 text objects** normalized to Arial;
- 📄 a layered searchable PDF;
- 🌐 an interactive HTML/SVG representation.

These values describe the original test case only and are **not hard-coded program limits**.

---

## 🤖 How the project was developed

The project was developed iteratively with the assistance of **ChatGPT**, using a real DXF exported from 3DEXPERIENCE.

The development process gradually added:

1. 🔎 DXF structure analysis;
2. 📐 automatic layer creation from text inside electrical-line blocks;
3. 🎨 `ByLayer` geometry and font normalization;
4. 🌐 an interactive HTML/SVG viewer;
5. 🖥️📱 desktop and mobile interaction improvements;
6. 📄 vector PDF generation with layers and searchable text;
7. ⚙️ a standalone Windows utility for batch processing.

ChatGPT was used as a development, analysis and rapid-prototyping tool. Once built, the utility operates independently.

---

## 🧰 Building the EXE from source

### Requirements

- Windows 10/11 x64;
- Python 3.11 x64 recommended;
- dependencies:
  - `ezdxf`;
  - `PyMuPDF`;
  - `PyInstaller` — required only for building the EXE.

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

The easiest build method on Windows is:

```text
BUILD_EXE_FIXED_V3.bat
```

The compiled executable will be created at:

```text
dist\3DE_Electrical_Utility_v5.exe
```

End users of the compiled EXE do not need Python installed.

---

## ⚠️ Project status

**Experimental / Prototype**

The utility is currently being tested on additional electrical schematics exported from 3DEXPERIENCE.

Before using generated files in a production workflow, always verify the results against the original schematic.

DXF structure may vary depending on:

- the 3DEXPERIENCE release;
- schematic templates;
- export settings;
- project-specific structures.

The recognition algorithm can be adapted if other DXF structures are encountered.

---

## 📥 Windows binary releases

Prebuilt Windows binaries should be distributed through **GitHub Releases** rather than committed directly into the source repository.

➡️ For normal use, download the ZIP containing `3DE_Electrical_Utility_v5.exe` from the appropriate Release.

---

## ℹ️ Disclaimer

This is an independent experimental project and is **not an official Dassault Systèmes product**.

CATIA and 3DEXPERIENCE are trademarks or registered trademarks of their respective owners.

---

## 📜 License

This project is distributed under the **MIT License**.

You may use, modify and distribute the source code in accordance with the license terms.

See [`LICENSE`](LICENSE) for details.
