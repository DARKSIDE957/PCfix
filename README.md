<div align="center">

# PCFIX · NECROMANCER EDITION

### Resurrect your PC — optimize, clean, repair, and diagnose in one place.

[![Version](https://img.shields.io/badge/version-v4.0-red?style=for-the-badge)](https://github.com/DARKSIDE957/PCfix/releases/tag/v4.0)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D6?style=for-the-badge&logo=windows11&logoColor=white)](https://github.com/DARKSIDE957/PCfix)
[![Python](https://img.shields.io/badge/python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

[**Download latest release**](https://github.com/DARKSIDE957/PCfix/releases/latest) · [**Report an issue**](https://github.com/DARKSIDE957/PCfix/issues)

*Beta — actively developed. Features and UI may change between releases.*

</div>

---

## What is PCFIX?

**PCFIX** is a Windows desktop toolkit for power users who want maintenance, tuning, and troubleshooting without juggling a dozen separate utilities. A dark OLED UI wraps deep system actions: registry tweaks, service controls, network fixes, debloating, force-delete tools, and a built-in **BSOD Analyzer** with crash history and repair shortcuts.

> **Run as Administrator** for full functionality. Many actions change system settings, services, or protected files.

---

## What's new in v4.0

- Redesigned **Necromancer** shell — true OLED blacks, crimson accents, grouped navigation
- Live metric cards with usage bars on the dashboard
- Persistent status bar and clearer page headers
- Installer and portable builds updated for **v4.0**

---

## Downloads

| File | Description |
|------|-------------|
| [**PCFIX_Setup_v4.0.exe**](https://github.com/DARKSIDE957/PCfix/releases/latest) | Recommended — installer with dependency checks, shortcuts, and `Program Files` install |
| [**PCFIX_v4.0.exe**](https://github.com/DARKSIDE957/PCfix/releases/latest) | Portable — single executable, no install |

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
| **Dashboard** | Live stats, Smart Scan, quick DNS/RAM/temp actions |
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

## Requirements

| Requirement | Notes |
|-------------|--------|
| **OS** | Windows 10 or 11 (64-bit) |
| **Privileges** | Administrator for most features |
| **VC++ Redistributable (x64)** | Installer can download if missing |
| **.NET Framework 4.8** | Installer can download if missing |
| **WebView2 Runtime (x64)** | Installer can download if missing |

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

**PCFIX NECROMANCER v4.0** · Made for Windows power users

[Star this repo](https://github.com/DARKSIDE957/PCfix) if it helped you

© 2026 PCFIX Development

</div>
