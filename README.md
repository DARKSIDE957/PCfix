<div align="center">

# PCFIX · NECROMANCER EDITION

### Resurrect your PC — optimize, clean, repair, and diagnose in one place.

[![Version](https://img.shields.io/badge/version-v3.10-red?style=for-the-badge)](https://github.com/DARKSIDE957/PCfix/releases/tag/v3.10)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D6?style=for-the-badge&logo=windows11&logoColor=white)](https://github.com/DARKSIDE957/PCfix)
[![Python](https://img.shields.io/badge/python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

[**Download latest release**](https://github.com/DARKSIDE957/PCfix/releases/latest) · [**Report an issue**](https://github.com/DARKSIDE957/PCfix/issues)

*Beta — actively developed. Features and UI may change between releases.*

</div>

---

## What is PCFIX?

**PCFIX** is a Windows desktop toolkit for power users who want maintenance, tuning, and troubleshooting without juggling a dozen separate utilities. A dark, modern UI wraps deep system actions: registry tweaks, service controls, network fixes, debloating, force-delete tools, and a built-in **BSOD Analyzer** with crash history and repair shortcuts.

> **Run as Administrator** for full functionality. Many actions change system settings, services, or protected files.

---

## Table of contents

- [Downloads](#downloads)
- [Features](#features)
- [App modules](#app-modules)
- [Quick start](#quick-start)
- [Build from source](#build-from-source)
- [Requirements](#requirements)
- [Troubleshooting](#troubleshooting)
- [Uninstall](#uninstall)
- [Disclaimer](#disclaimer)
- [License](#license)

---

## Downloads

| File | Description |
|------|-------------|
| [**PCFIX_Setup_v3.10.exe**](https://github.com/DARKSIDE957/PCfix/releases/latest) | Recommended — installer with dependency checks, shortcuts, and `Program Files` install |
| [**PCFIX_v3.10.exe**](https://github.com/DARKSIDE957/PCfix/releases/latest) | Portable — single executable, no install |

1. Open **[Releases](https://github.com/DARKSIDE957/PCfix/releases)** and download the build you need.
2. Run the installer **or** the portable `.exe` **as Administrator**.
3. Launch from the Desktop shortcut, Start Menu, or the portable file directly.

---

## Features

<table>
<tr>
<td width="50%" valign="top">

### System & performance
- Live **CPU, RAM, disk** (and battery on laptops)
- **Smart Scan** — one-click clean, DNS flush, RAM optimize
- **Tweaks** — gaming, power, Explorer, telemetry, Copilot, and more
- **Boost** — high-performance plan, GPU priority, visual tweaks
- **Startup manager** — enable/disable boot apps
- **Specs** — CPU, GPU, OS build, uptime; export to file

</td>
<td width="50%" valign="top">

### Repair & recovery
- **SFC** and **DISM** from the UI
- **CHKDSK** scheduling and **memory diagnostic** launcher
- **BSOD Analyzer** — event log history, bugcheck explanations, dump analysis
- **Restore point** creation and settings export

</td>
</tr>
<tr>
<td valign="top">

### Clean & debloat
- Temp purge, recycle bin, Windows Update cache
- **Debloat** — scan and remove common preinstalled apps
- **Force Remove App** — find artifacts, quarantine-delete, restore
- **Unlocker** — delete locked files and folders

</td>
<td valign="top">

### Network & privacy
- DNS presets (Cloudflare, Google, OpenDNS, DHCP restore)
- Flush DNS, Winsock reset, adapter reset, ping tests
- Privacy toggles and **Privacy Shield** telemetry reduction
- Optional IP/MAC hide in the network view

</td>
</tr>
</table>

---

## App modules

| Section | What it does |
|---------|----------------|
| **Dashboard** | Live stats, Smart Scan, quick DNS/RAM actions |
| **Cleaner** | Deep cleaning toggles, services, privacy, gaming |
| **Repair** | SFC, DISM, network stack reset, disk check |
| **Boost** | Performance plan and GPU-oriented shortcuts |
| **Tweaks** | Advanced registry and system optimizations |
| **Startup** | Control programs that run at login |
| **Specs** | Hardware and OS information |
| **Tools** | DNS switcher, hosts, firewall helpers |
| **Network** | Adapters, DNS, latency, privacy display |
| **Privacy** | Telemetry and tracking-related controls |
| **Debloat** | Remove bundled Windows apps |
| **Unlocker** | Force-delete stubborn files |
| **Force Remove** | Hunt and remove leftover app data |
| **BSOD Analyzer** | Crashes, insights, dumps, export report |
| **Settings** | Tray minimize, startup sound, auto RAM optimize |

---

## Quick start

### Using the release build
1. Install or run **`PCFIX_Setup_v3.10.exe`** / **`PCFIX_v3.10.exe`** as Administrator.
2. Open **Tweaks** or **Cleaner** and enable only what you understand — each switch includes a short description and risk note.
3. Reboot after major system or service changes.

### Running from source
```bash
git clone https://github.com/DARKSIDE957/PCfix.git
cd PCfix
pip install -r requirements.txt
python main.py
```

| Command | Result |
|---------|--------|
| `python main.py` | Full **CustomTkinter** desktop app (default) |
| `python main.py --webview` | Lighter Chromium-based shell |
| `set PCFIX_UI=webview` | Same as `--webview` on Windows |
| `python bsod_cli.py path\to\dump.dmp` | Analyze crash dumps from the terminal |
| `python scripts/health_check.py` | Quick API smoke test |

**Config file:** `%LOCALAPPDATA%\PCFIX\config.json`

---

## Build from source

```bash
pip install -r requirements.txt
python build.py --no-tester
```

Outputs in `dist/`:
- `PCFIX_v3.10.exe` — portable app  
- `PCFIX_Setup_v3.10.exe` — installer (bundles the app exe)

---

## Requirements

| Requirement | Notes |
|-------------|--------|
| **OS** | Windows 10 or 11 (64-bit) |
| **Privileges** | Administrator for most features |
| **VC++ Redistributable (x64)** | Installer can download if missing |
| **.NET Framework 4.8** | Installer can download if missing |
| **WebView2 Runtime (x64)** | Optional; used only for `--webview` UI |

---

## Troubleshooting

<details>
<summary><strong>App won’t start</strong></summary>

- Install **VC++ x64**, **.NET 4.8**, and **WebView2**, then retry.
- Right-click the `.exe` → **Run as administrator**.
- Check `%LOCALAPPDATA%\PCFIX\pcfix.log` for errors.

</details>

<details>
<summary><strong>Tweaks didn’t apply</strong></summary>

- Reboot after registry or service changes.
- Confirm antivirus or Group Policy isn’t blocking edits.

</details>

<details>
<summary><strong>BSOD tools show nothing</strong></summary>

- Run as Administrator.
- You need a recent crash in the System log (Event ID 1001) or a `.dmp` file for advanced analysis.

</details>

---

## Uninstall

1. Close PCFIX (exit from tray if minimized).
2. Delete `C:\Program Files\PCFIX` (or your custom install folder).
3. Remove Desktop and Start Menu shortcuts.
4. Optional: delete registry key `HKCU\Software\PCFIX`.
5. Optional: delete `%LOCALAPPDATA%\PCFIX` for logs and config.

---

## Disclaimer

PCFIX can modify system settings, services, registry, and files. **You are responsible for your machine.** Back up important data and create a restore point before applying aggressive tweaks.

---

## License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE).

---

<div align="center">

**PCFIX NECROMANCER v3.10** · Made for Windows power users

[Star this repo](https://github.com/DARKSIDE957/PCfix) if it helped you

© 2026 PCFIX Development

</div>
