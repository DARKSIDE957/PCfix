![Version](https://img.shields.io/badge/version-v3.10-red)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

# PCFIX | NECROMANCER EDITION v3.10

**Status: Beta – still in active development. Features may change.**

**The Ultimate System Optimization & Repair Tool**

**RESURRECT YOUR PC** with high-performance optimization, deep cleaning, and advanced diagnostics.

---


## 🔥 Key Features

### ⚡ System Mastery
- **Hardware Insight:** Deep scan analysis of CPU, GPU, RAM, and motherboard metrics. Reveal what Windows hides.
- **AI Auto-Pilot:** One-click smart optimization. Clean, boost, and repair your system instantly.
- **Force Cleaner:** Obliterate locked files and stubborn folders that refuse to be deleted.

### 🌐 Network Commander
- **Real-time Latency Monitoring:** Keep track of your ping and connection stability.
- **DNS Switcher:** Instantly switch between Google, Cloudflare, and OpenDNS for faster browsing.
- **Privacy Mode:** Hide your IP and MAC address with a single click.
- **Adapter Reset:** Flush DNS and reset network adapters to fix connectivity issues.

### ☠️ BSOD Analyzer
- **Crash Log Decoder:** Don't fear the Blue Screen. Decode it.
- **Auto-Fix:** Suggested fixes for common critical errors like `CRITICAL_PROCESS_DIED`.
- **System Repair Tools:** Integrated SFC Scan, CHKDSK, and Memory Diagnostic tools.

---

## 🛠️ Installation

1. Download the latest `PCFIX_Setup.exe` from the [Releases page](../../releases).
2. Run the installer and follow the on-screen instructions.
3. Launch PCFIX from your desktop or start menu.

---

## ⚡ Quick Start

- Run PCFIX as Administrator for full functionality (`python main.py` launches the full desktop UI).
- Optional Chromium shell: `python main.py --webview` or set `PCFIX_UI=webview`.
- Open “🧩 Tweaks” and enable only what you need. Each toggle shows a short description and risk note.
- Use “CLEANING PROTOCOLS” to free space safely, then reboot.
- For BSOD issues, open “BSOD ANALYZER”, view details, and export a report.
- Settings are stored in `%LOCALAPPDATA%\PCFIX\config.json`.

---

## ✅ Requirements

- Windows 10 or 11 (x64)
- Administrator rights for system changes
- Dependencies (installer can auto‑install if missing):
  - Microsoft Visual C++ Redistributable (x64)
  - .NET Framework 4.8
  - Microsoft Edge WebView2 Runtime (x64)

---

## ⚠️ Disclaimer

By using PCFIX you accept that any actions you take with the app are your own responsibility. Proceed with care and back up important data before applying system changes.

---

## 🧩 Troubleshooting

- PCFIX doesn’t start:
  - Install VC++ x64, .NET 4.8, and WebView2, then try again.
  - Right‑click → Run as Administrator.
- Tweaks didn’t apply:
  - Reboot after applying system/service changes.
  - Check that antivirus or group policies aren’t blocking registry edits.
- BSOD tools:
  - Some logs require admin and recent crashes to appear.

---

## 🗑️ Uninstall

- Close PCFIX.
- Remove the install folder (default: `C:\Program Files\PCFIX`).
- Delete shortcuts from Desktop and Start Menu if needed.
- Optional: Remove `HKCU\Software\PCFIX` registry key.

---

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

&copy; 2026 PCFIX Development. All systems nominal.
