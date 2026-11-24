<div align="center">

# PCFIX · NECROMANCER EDITION v4.1

### Resurrect your PC — repair, clean, optimize, and diagnose Windows in one native toolkit.

[![Version](https://img.shields.io/badge/version-v4.1-E11D48?style=for-the-badge)](https://github.com/DARKSIDE957/PCfix/releases/tag/v4.1)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11%20x64-0078D6?style=for-the-badge&logo=windows11&logoColor=white)](https://github.com/DARKSIDE957/PCfix)
[![Runtime](https://img.shields.io/badge/native-.NET%208%20WPF-512BD4?style=for-the-badge&logo=dotnet&logoColor=white)](https://github.com/DARKSIDE957/PCfix/releases/latest)
[![License](https://img.shields.io/badge/license-MIT-22C55E?style=for-the-badge)](https://github.com/DARKSIDE957/PCfix)

[**Download Latest Release (v4.1)**](https://github.com/DARKSIDE957/PCfix/releases/latest) · [**All Releases**](https://github.com/DARKSIDE957/PCfix/releases) · [**Report an Issue**](https://github.com/DARKSIDE957/PCfix/issues)

</div>

---

## What is PCFIX?

**PCFIX Necromancer v4.1** is a fast, self-contained native Windows toolkit designed to fix sluggish, crashed, or cluttered PCs without installing a dozen separate utilities. Wrapped in a frameless **OLED Black & Crimson** interface with instant startup and a live operation console, it gives you real Windows diagnostics, deep cleaning, system file repair, driver checks, network tuning, debloating, and crash analysis in one place.

> **Administrator privileges** are requested automatically on launch so repairs like SFC, DISM, Windows Update reset, DNS switching, and service recovery work cleanly out of the box.

---

## Downloads (v4.1)

| Download | Best For | Notes |
|----------|----------|-------|
| [**PCFIX_Setup_v4.1.exe**](https://github.com/DARKSIDE957/PCfix/releases/latest) | **Recommended** | Standalone single-file installer. Installs to Program Files, creates Desktop & Start Menu shortcuts, registers in Windows Apps & Features with clean Uninstall support. |
| [**PCFIX_v4.1_Portable.zip**](https://github.com/DARKSIDE957/PCfix/releases/latest) | **USB / Portable** | Zero installation required. Extract the folder anywhere and run `PCFIX.exe`. Self-contained — no Python or extra runtimes needed. |

1. Open [**Releases**](https://github.com/DARKSIDE957/PCfix/releases/latest) and download **PCFIX_Setup_v4.1.exe** or **PCFIX_v4.1_Portable.zip**.
2. Run the standalone installer (or unzip the portable folder and launch `PCFIX.exe`).
3. Click **Run Smart Heal** on the Command Center to scan and fix your PC in one pass.

---

## What's New in v4.1

- **Instant Native Launch** — Eliminated startup freezes and Perflib delays (`GetSystemTimes` + ReadyToRun AOT compilation) and fixed the launch crash completely.
- **Standalone Single-File Setup Installer** — Completely rebuilt `PCFIX_Setup_v4.1.exe` with embedded payload, custom install directory picker, Desktop/Start Menu shortcuts, and full Windows Apps & Features uninstaller.
- **11-Category Scan-First Deep Cleaner + Real RAM Trimmer** — Measures exact reclaimable space across Windows Temp, Browser Caches, DirectX/NVIDIA/AMD Shader Caches, Recycle Bin, Crash Dumps, Delivery Optimization, Update Cache, and more — plus real Win32 working-set trimming across active processes.
- **True System Repair Suite with Live Console** — 15-point Health Diagnostic plus async streaming `sfc /scannow`, `DISM /RestoreHealth`, `DISM /StartComponentCleanup`, full Windows Update stack reset, online `chkdsk /scan`, SSD TRIM, Print Spooler reset, Microsoft Store reset, Time sync, and System Restore Point management.
- **Drivers & Processes Monitors** — Detect Device Manager error codes (Code 10, 28, 43, etc.) with plain-English fixes, browse signed drivers, inspect top RAM consumers, and detect file-locking processes via the Windows Restart Manager API.
- **Modern OLED Crimson Shell** — Redesigned frameless Windows 11/10 shell with `Ctrl+K` Global Quick Search, toggle switches, dark scrollbars, collapsible live console with Cancel support, real System Tray mode, and live-synced Windows Tweaks & Privacy Shield.

---

## Feature Overview

<table>
<tr>
<td width="50%" valign="top">

### Fix & Diagnose
- **15-Point Health Scan** — Services, drives, SMART status, faulty drivers, firewall, hosts/proxy hijacks, pending reboots, and crash history
- **Deep Repairs** — Live streaming **SFC**, **DISM RestoreHealth**, **WinSxS Cleanup**, **Windows Update Reset**, **chkdsk /scan**, **SSD TRIM**, **Print Spooler**, **Store Reset**, and **Explorer Rebuild**
- **Drivers & Devices** — Device Manager error code inspector + signed driver inventory & export
- **BSOD Analyzer** — Stop-code diagnosis database, Event Log crash timeline, and `.dmp` minidump inspector

</td>
<td width="50%" valign="top">

### Clean, Optimize & Shield
- **Deep Cleaner** — 11 scan-first categories (Temp, Browser caches, GPU Shader caches, Thumbnails, WER/Dumps, Recycle Bin, Update cache, Prefetch, Logs)
- **Processes & RAM** — Live memory monitor, process terminator, and real Win32 working-set trimmer
- **Performance Boost** — Gaming Ultimate, Workstation, Quiet/Eco, and Balanced Default profiles with live power plan detection
- **16 Windows Tweaks** — HAGS, Game Mode, Game DVR off, Raw Mouse, Win11 Classic Context Menu, Bing/Copilot off, Fast Startup off, Hibernation toggle, and more

</td>
</tr>
<tr>
<td valign="top">

### Control & Debloat
- **Debloater** — Categorized Windows 10/11 AppX bloat removal with optional all-user provisioned removal
- **Startup & Services** — Manage Registry & Startup folder entries (disabled items stay recoverable) plus quick control over heavy Windows services
- **File Unlocker** — Inspect which process locks a stubborn file (Restart Manager), kill lockers, force delete, or safely quarantine
- **Force Remove App** — Scan Program Files, AppData, ProgramData, and Uninstall registry for app leftovers

</td>
<td valign="top">

### Network & Privacy
- **Parallel DNS Benchmark** — Ping Cloudflare, Google, Quad9, AdGuard, and OpenDNS side-by-side and apply the fastest in one click
- **Network Stack Repair** — Flush DNS, IP lease renew, full Winsock + TCP/IP reset, listening TCP ports viewer, and IP/MAC privacy masking
- **Privacy Shield** — 12 live-verified registry policies (Telemetry, DiagTrack, Recall AI snapshots, Ad ID, Activity History, Cloud Clipboard, God Mode)
- **Hosts & Utilities** — Auto-backed-up hosts editor + 12 built-in Windows diagnostic launchers

</td>
</tr>
</table>

---

## Requirements

| Requirement | Details |
|-------------|---------|
| **OS** | Windows 10 or Windows 11 (64-bit / x64) |
| **Privileges** | Administrator (prompted automatically via UAC) |
| **Dependencies** | **None** — self-contained native .NET 8 build |
