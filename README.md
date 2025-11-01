# VN PCfix

VN PCfix is a modular PowerShell toolkit for Windows troubleshooting and repair. It provides a clean console UI with theming, diagnostics panels, and safe repair actions with comprehensive logging and `-WhatIf` dry-run support.

## Purpose & Functionality
- Interactive console with main and repair menus
- System diagnostics: OS, CPU, memory, disk info, recent critical events
- Repair actions: `SFC`, `DISM`, `CHKDSK` scan/fix
- Logging to `%LocalAppData%\PCfix\pcfix-<timestamp>.log`
- Accessibility and appearance options: high-contrast, no-color, ASCII icons, large text

## Usage
```powershell
powershell -ExecutionPolicy Bypass -File .\PCfix.ps1
powershell -ExecutionPolicy Bypass -File .\PCfix.ps1 -WhatIf
powershell -ExecutionPolicy Bypass -File .\PCfix.ps1 -HighContrast -BasicASCII
```

### Parameters
- `-NoElevate`: Do not auto-elevate; restrict repairs in non-admin sessions
- `-HighContrast`: Force high-contrast colors
- `-NoColor`: Disable all color output
- `-BasicASCII`: Use ASCII symbols to avoid encoding issues
- `-LargeText`: Add spacing for readability
- `-WhatIf`: Dry-run actions; supported for all repairs

## Dependencies
- PowerShell `5.1` or `7.x`
- Windows 10/11 (for DISM/Defender modules)
- Pester (tests) — PowerShell 5.1 ships Pester 3.x by default; tests target basic DSL

## Configuration
Optional JSON: `config\vnpcfix.json`
```json
{
  "UI": {
    "HighContrast": false,
    "NoColor": false,
    "BasicASCII": true,
    "LargeText": false
  }
}
```
Applied on startup if present; command-line flags override config.

## Security Best Practices
- Least-privilege by default; repairs require Admin and prompt elevation
- `SupportsShouldProcess` on repair functions for `-WhatIf` and confirmation flows
- Input validation and guarded file system operations
- No use of `Invoke-Expression`; external commands invoked explicitly
- Logs stored under `%LocalAppData%\PCfix` (per-user)

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
assets/logo-vnpcfix.svg   # Brand asset
tests/                    # Pester tests (unit)
```

## Compatibility
- PowerShell 5.1 and 7.x
- Handles non-UTF8 consoles with ASCII fallbacks

## License
Copyright © 2025 VN PCfix. All rights reserved.