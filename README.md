# VN PCfix

 

[![PowerShell 5.1+](https://img.shields.io/badge/PowerShell-5.1%2B-blue)](https://learn.microsoft.com/powershell/scripting/overview)
[![Windows 10/11](https://img.shields.io/badge/Windows-10%2F11-blue)](https://www.microsoft.com/windows)
[![Run from GitHub](https://img.shields.io/badge/Run-irm%20%7C%20iex-lightgrey)](https://raw.githubusercontent.com/DARKSIDE957/PCfix/main/PCfix.ps1)
[![Support on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/C0C3RZTLR)

Copy & Run now (run in PowerShell as Administrator):

```powershell
iex (irm 'https://raw.githubusercontent.com/DARKSIDE957/PCfix/main/PCfix.ps1')
```

VN PCfix is a modular PowerShell toolkit for Windows troubleshooting and repair. It provides a clean console UI with theming, diagnostics panels, and safe repair actions with comprehensive logging and `-WhatIf` dry-run support.

## Purpose & Functionality
- Interactive console with main and repair menus
- System diagnostics: OS, CPU, memory, disk info, recent critical events
- Repair actions: `SFC`, `DISM`, `CHKDSK` scan/fix
- Logging to `%LocalAppData%\PCfix\pcfix-<timestamp>.log`
- Accessibility and appearance options: high-contrast, no-color, ASCII icons, large text

 



## Dependencies
- PowerShell `5.1` or `7.x`
- Windows 10/11 (for DISM/Defender modules)


## Project Structure
```
PCfix.ps1                 # Entry script (imports module)
src/                      # PowerShell module and components
  VNPCfix.psd1            # Module manifest
  VNPCfix.psm1            # Module aggregator
  VNPCfix.Core.psm1       # State, logging, config
  VNPCfix.UI.psm1         # UI helpers and theming
  VNPCfix.Security.psm1   # Admin checks and elevation
  VNPCfix.Diagnostics.psm1# Diagnostics panels
  VNPCfix.Repairs.psm1    # Repairs (SFC, DISM, CHKDSK)
```

## Compatibility
- PowerShell 5.1 and 7.x
- Handles non-UTF8 consoles with ASCII fallbacks

## License
Copyright © 2025 VN PCfix. All rights reserved.
