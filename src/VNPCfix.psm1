Set-StrictMode -Version Latest

Import-Module (Join-Path $PSScriptRoot 'VNPCfix.Core.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'VNPCfix.UI.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'VNPCfix.Security.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'VNPCfix.Diagnostics.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'VNPCfix.Repairs.psm1') -Force

function Start-VNPCfix {
  [CmdletBinding(SupportsShouldProcess)]
  param(
    [switch]$NoElevate,
    [switch]$HighContrast,
    [switch]$NoColor,
    [switch]$BasicASCII,
    [switch]$LargeText
  )

  # Initialize state
  $whatIfSwitch = [bool]$WhatIfPreference
  Set-VNPCfixOptions -HighContrast:$HighContrast -NoColor:$NoColor -BasicASCII:$BasicASCII -LargeText:$LargeText
  $cfg = Get-VNPCfixConfig
  if ($cfg) { Apply-VNPCfixConfig -Config $cfg }
  Initialize-Theme -HighContrast:$HighContrast -NoColor:$NoColor -BasicASCII:$BasicASCII -LargeText:$LargeText
  Initialize-Logging
  $isAdmin = Test-IsAdmin
  $title = 'VN PCfix – Windows Troubleshooting & Repair'
  Show-Header -Title $title -LogFile $script:State.LogFile -SessionStamp $script:State.SessionStamp -IsAdmin:$isAdmin

  # Elevation path
  if (-not $NoElevate -and -not $isAdmin) {
    Write-Status Warning 'Repairs require elevation; some actions may be unavailable.'
  }

  # Main menu loop
  while ($true) {
    Write-Title 'Main Menu'
    Write-Separator
    Format-MenuItem 1 'Diagnostics'
    Format-MenuItem 2 'Repairs (requires Admin)'
    Format-MenuItem 0 'Exit'
    Write-Status Info 'Tip: Use -WhatIf to dry-run most actions.'
    if (-not $isAdmin) { Write-Status Warning 'Some actions require Administrator privileges.' }
    $choice = Read-Host 'Select an option'
    switch ($choice) {
      '1' {
        try { Invoke-VNPCfixDiagnostics } catch {}
      }
      '2' {
        if (-not $isAdmin) {
          Write-Status Warning 'Repairs require Admin. Attempting elevation...'
          $args = @('-ExecutionPolicy','Bypass','-File', (Join-Path (Split-Path -Parent $PSScriptRoot) 'PCfix.ps1'))
          $argStr = $args -join ' '
          if (Request-Elevation -ScriptPath 'powershell.exe' -Args $argStr) { break }
          Write-Status Error 'Elevation cancelled or failed. Use -NoElevate to preview.'
          continue
        }
        Write-Title 'Repairs'
        Write-Separator
        Format-MenuItem 1 'Run SFC (System File Checker)'
        Format-MenuItem 2 'Run DISM RestoreHealth'
        Format-MenuItem 3 'Run CHKDSK scan'
        Format-MenuItem 4 'Run CHKDSK fix'
        Format-MenuItem 5 'Reset Winsock & IP stack'
        Format-MenuItem 6 'Reset Windows Update components'
        Format-MenuItem 7 'DISM StartComponentCleanup (WinSxS)'
        Format-MenuItem 8 'Clear TEMP folders'
        Format-MenuItem 9 'Registry repair (Windows Installer re-register)'
        Format-MenuItem 10 'Create a system restore point'
        Format-MenuItem 11 'Rollback Windows Update cache rename'
        Format-MenuItem 12 'Flush DNS and renew IP'
        Format-MenuItem 13 'Reset Windows Firewall to default'
        Format-MenuItem 14 'Reset Microsoft Store cache'
        Format-MenuItem 15 'Rebuild Windows Search index'
        Format-MenuItem 16 'Resync Windows Time service'
        Format-MenuItem 0 'Back'
        $r = Read-Host 'Select a repair'
        switch ($r) {
          '1' { try { Invoke-VNPCfixSfcRepair -WhatIf:$whatIfSwitch } catch {} }
          '2' { try { Invoke-VNPCfixDismRepair -WhatIf:$whatIfSwitch } catch {} }
          '3' { try { Invoke-VNPCfixChkdskScan -WhatIf:$whatIfSwitch } catch {} }
          '4' { try { Invoke-VNPCfixChkdskFix -WhatIf:$whatIfSwitch } catch {} }
          '5' { try { Invoke-VNPCfixWinsockReset -WhatIf:$whatIfSwitch } catch {} }
          '6' { try { Invoke-VNPCfixWindowsUpdateReset -WhatIf:$whatIfSwitch } catch {} }
          '7' { try { Invoke-VNPCfixStartComponentCleanup -WhatIf:$whatIfSwitch } catch {} }
          '8' { try { Invoke-VNPCfixClearTempFiles -WhatIf:$whatIfSwitch } catch {} }
          '9' { try { Invoke-VNPCfixRegistryRepair -WhatIf:$whatIfSwitch } catch {} }
          '10' { try { Invoke-VNPCfixCreateRestorePoint -WhatIf:$whatIfSwitch } catch {} }
          '11' { try { Invoke-VNPCfixWindowsUpdateCacheRestore -WhatIf:$whatIfSwitch } catch {} }
          '12' { try { Invoke-VNPCfixFlushDnsAndRenewIp -WhatIf:$whatIfSwitch } catch {} }
          '13' { try { Invoke-VNPCfixResetFirewall -WhatIf:$whatIfSwitch } catch {} }
          '14' { try { Invoke-VNPCfixResetWindowsStoreCache -WhatIf:$whatIfSwitch } catch {} }
          '15' { try { Invoke-VNPCfixRebuildSearchIndex -WhatIf:$whatIfSwitch } catch {} }
          '16' { try { Invoke-VNPCfixResyncTimeService -WhatIf:$whatIfSwitch } catch {} }
          '0'  { Write-Status Info 'Returning to main menu.' }
          default { Write-Status Warning 'Invalid selection.' }
        }
      }
      '0' { Write-Status Info 'Goodbye.'; return }
      default { Write-Status Warning 'Invalid selection.' }
    }
  }
}

Export-ModuleMember -Function Start-VNPCfix, Set-VNPCfixOptions, Write-Log, Invoke-VNPCfixDiagnostics, Invoke-VNPCfixSfcRepair, Invoke-VNPCfixDismRepair, Invoke-VNPCfixChkdskScan, Invoke-VNPCfixChkdskFix, Invoke-VNPCfixWinsockReset, Invoke-VNPCfixWindowsUpdateReset, Invoke-VNPCfixStartComponentCleanup, Invoke-VNPCfixClearTempFiles, Invoke-VNPCfixRegistryRepair, Invoke-VNPCfixCreateRestorePoint, Invoke-VNPCfixWindowsUpdateCacheRestore, Invoke-VNPCfixFlushDnsAndRenewIp, Invoke-VNPCfixResetFirewall, Invoke-VNPCfixResetWindowsStoreCache, Invoke-VNPCfixRebuildSearchIndex, Invoke-VNPCfixResyncTimeService