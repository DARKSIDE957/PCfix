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
- Enhanced diagnostics: service health (WUA, BITS, CryptSvc, MSI),
  network reachability checks (DNS/HTTPS), storage health overview, optional
  `DISM /CheckHealth` in full mode
- Repair actions: `SFC`, `DISM RestoreHealth`, `CHKDSK` scan/fix
- Additional repairs: Winsock/IP stack reset, Windows Update components reset,
  DISM StartComponentCleanup (WinSxS), clear TEMP folders
  New: DNS flush & IP renew, reset Windows Firewall, reset Microsoft Store cache,
  rebuild Windows Search index, resync Windows Time service
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

## New Additions & Specifications
- Functionality
  - `Invoke-VNPCfixDiagnostics [-FullChecks]` outputs panels and returns a structured summary object with keys: `SystemInfo`, `Services`, `Network`, `Storage`, `Events`, and optional `DismCheckHealth`.
  - Quick mode (default) avoids long-running checks; Full mode adds `DISM /CheckHealth`.
- Design Guidelines
  - Use existing UI helpers (`Write-Panel`, `Write-Title`, `Write-Separator`, `Write-Status`) for consistent console output.
  - Keep actions idempotent and non-destructive in diagnostics.
- Technical Constraints
  - PowerShell 5.1+, Windows 10/11; no external dependencies.
  - Prefer CIM/WMI (`Get-CimInstance`) fallbacks when modern cmdlets are unavailable.
  - Repairs support `-WhatIf` via `SupportsShouldProcess`.
- Performance Expectations
  - Quick diagnostics complete under ~10s on typical systems.
  - Full diagnostics (with DISM check) under ~2 minutes depending on system.
- Testing Requirements
  - Pester tests verify module loading, exports, and that diagnostics returns a summary object without running heavy operations.
  - Manual validation: run `Invoke-VNPCfixDiagnostics -FullChecks` and review panels and log entries.

## Usage Examples
```powershell
# Start interactive UI (recommended)
Start-VNPCfix

# Quick diagnostics (non-destructive)
Invoke-VNPCfixDiagnostics

# Full diagnostics including DISM CheckHealth
Invoke-VNPCfixDiagnostics -FullChecks

# Run repairs with dry-run preview
Invoke-VNPCfixDismRepair -WhatIf
Invoke-VNPCfixSfcRepair -WhatIf
Invoke-VNPCfixFlushDnsAndRenewIp -WhatIf
Invoke-VNPCfixResetFirewall -WhatIf
Invoke-VNPCfixResetWindowsStoreCache -WhatIf
Invoke-VNPCfixRebuildSearchIndex -WhatIf
Invoke-VNPCfixResyncTimeService -WhatIf
```

## Compatibility
- PowerShell 5.1 and 7.x
- Handles non-UTF8 consoles with ASCII fallbacks

## License
Copyright © 2025 VN PCfix. All rights reserved.
