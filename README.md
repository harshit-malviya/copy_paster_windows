# ⚡ Click-to-Paste Automation Tool

A modern Windows automation application that sequentially pastes items from your data list whenever you left-click your mouse. It includes custom click/skip pattern logic, safety window-boundary checks, and global hotkeys.

---

## ✨ Features

- **Sequential Left-Click Pasting**: Automatically pastes the next item from your queue into whichever external application (Excel, SAP, Web Browser, CRM, ERP, Notepad) you left-click into.
- **Dual Automation Modes**:
  - **Manual Click Mode**: You click where you want; the tool pastes sequentially from your queue based on your skip pattern.
  - **Auto-Clicker Mode**: The application automatically moves your mouse cursor, clicks at defined screen locations, and pastes entries one-by-one.
- **Interactive Coordinate Capture (F7)**:
  - In Auto-Clicker mode, simply hover your mouse over any input box or button on your screen and press **`F7`** to record its `(X, Y)` position instantly.
- **Multi-Point Sequences per Item**:
  - Define 1 or multiple points per entry (e.g., Point 1: *Click & Paste*, Point 2: *Click Submit/Next Button*).
- **Custom Skip Pattern Sequences (Manual Mode)**:
  - `P` : Pastes on every left click.
  - `P, S` : 1st click pastes, 2nd click skips, 3rd click pastes (alternating clicks).
  - `P, S, S` : 1st click pastes, next 2 clicks skip, 4th click pastes (1 in 3 clicks).
  - Any custom sequence like `P, S, P, S, S` can be typed in!
- **Data Ingestion**:
  - File Import: supports `.txt` (one per line), `.csv`, and Excel `.xlsx` / `.xlsm`.
  - Custom Text Paste dialog (paste text directly into queue with optional "Skip header" toggle).
- **Safety Window-Boundary Detection**:
  - Clicks made inside the Click-to-Paste application window (clicking buttons, scrolling, adjusting settings) are **automatically ignored** so they never consume an item or paste into the app.
- **Global Hotkeys**:
  - `F7`: Grab & record mouse coordinate under cursor.
  - `F8`: Toggle active state (Start / Pause).
  - `Esc`: Emergency stop (instantly aborts automation).
- **Timing & Post-Paste Actions**:
  - Auto-Clicker pacing slider (0.2s – 5.0s between items).
  - Focus delay slider (20ms – 400ms, default 80ms) to ensure target input fields gain focus before text insertion.
  - Post-paste keystroke: `None (Just Paste)`, `Press Tab`, `Press Enter`, or `Press Down Arrow`.
  - Audio confirmation beeps (distinct frequencies for Paste vs Skip).
- **Always-on-Top Toggle**:
  - Keep the app floating over your working windows to monitor progress.

---

## 🚀 Quick Start

### Option 1: Run with Batch File (Automatic Setup)
Simply double-click **`run.bat`**. It will:
1. Create a Python virtual environment (`.venv`).
2. Automatically install all required packages (`customtkinter`, `pynput`, `pyperclip`, `openpyxl`, `pyinstaller`).
3. Launch the application!

### Option 2: Run via Terminal
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## 📦 Building a Standalone Executable (.exe)

### Option 1: Automatic Build (Batch Script)
Simply double-click **`build_exe.bat`**.

---

### Option 2: Manual Build via Terminal

Make sure your virtual environment is active:
```powershell
.\.venv\Scripts\activate
```

#### Method A: Directory-based Build (Fast startup & recommended)
```powershell
pyinstaller --noconfirm --onedir --windowed --name "ClickToPaste" --collect-all "customtkinter" main.py
```
> The output executable will be located in:  
> `dist\ClickToPaste\ClickToPaste.exe`

#### Method B: Single-file Executable (Portable single `.exe`)
```powershell
pyinstaller --noconfirm --onefile --windowed --name "ClickToPaste" --collect-all "customtkinter" main.py
```
> The standalone executable will be located in:  
> `dist\ClickToPaste.exe`

---

## 🎯 How to Use

### Mode A: Manual Click Mode
1. **Load Your Data**: Click **"📁 Import File..."** or **"📋 Paste Text / Queue"**.
2. **Set Pattern**: Choose **`P, S`** for alternating clicks (paste on 1st click, skip on 2nd click).
3. **Arm Automation**: Press **`F8`** or click **▶ START AUTOMATION**.
4. **Click into Fields**: Left-click into your target software (Excel, SAP, Browser) — it pastes automatically!

### Mode B: Auto-Clicker Mode (Defined Screen Locations)
1. **Switch Tab**: Click the **🤖 Auto-Clicker Mode** tab at the top right.
2. **Define Screen Points**:
   - Hover your mouse over your target input field on screen and press **`F7`** to record Point #1 (set to *Click & Paste Item*).
   - (Optional) Hover your mouse over a "Submit" or "Next" button and press **`F7`** to record Point #2 (set to *Just Click*).
3. **Set Interval**: Adjust the **Interval Between Items** slider (e.g. 1.0s).
4. **Run**: Press **`F8`** or click **▶ START AUTO-CLICKER**. The tool automatically loops through your items, clicking and pasting into each defined coordinate!
5. **Emergency Stop**: Press **`Esc`** at any second to immediately abort.
