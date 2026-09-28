# ⚡ Click-to-Paste Automation Tool

A modern Windows automation application that sequentially pastes items from your data list whenever you left-click your mouse. It includes custom click/skip pattern logic, safety window-boundary checks, and global hotkeys.

---

## ✨ Features

- **Sequential Left-Click Pasting**: Automatically pastes the next item from your queue into whichever external application (Excel, SAP, Web Browser, CRM, ERP, Notepad) you left-click into.
- **Custom Skip Pattern Sequences**:
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
  - `F8`: Toggle active state (Arm / Pause).
  - `Esc`: Emergency stop (instantly disarms).
- **Timing & Post-Paste Actions**:
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

1. **Load Your Data**:
   - Click **"📁 Import File..."** to load a `.txt`, `.csv`, or `.xlsx` file, or click **"📋 Paste Text / Queue"** to paste rows directly from your clipboard.
2. **Select or Configure Your Pattern**:
   - For alternate clicks (paste, then don't paste, then paste), choose **`P, S`**.
3. **Start Automation**:
   - Click **▶ START AUTOMATION** or press **`F8`** on your keyboard.
   - The status bar turns into active mode.
4. **Click in Target Field**:
   - Left-click into your target input cell or text box in Excel, SAP, browser, etc.
   - The value is automatically pasted and the step advances!
5. **Pause or Finish**:
   - Press **`F8`** anytime to pause, or **`Esc`** to stop.
