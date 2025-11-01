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
        Format-MenuItem 0 'Back'
        $r = Read-Host 'Select a repair'
        switch ($r) {
          '1' { try { Invoke-VNPCfixSfcRepair -WhatIf:$whatIfSwitch } catch {} }
          '2' { try { Invoke-VNPCfixDismRepair -WhatIf:$whatIfSwitch } catch {} }
          '3' { try { Invoke-VNPCfixChkdskScan -WhatIf:$whatIfSwitch } catch {} }
          '4' { try { Invoke-VNPCfixChkdskFix -WhatIf:$whatIfSwitch } catch {} }
          default { Write-Status Info 'Returning to main menu.' }
        }
      }
      '0' { Write-Status Info 'Goodbye.'; break }
      default { Write-Status Warning 'Invalid selection.' }
    }
  }
}

Export-ModuleMember -Function Start-VNPCfix, Set-VNPCfixOptions, Write-Log, Invoke-VNPCfixDiagnostics, Invoke-VNPCfixSfcRepair, Invoke-VNPCfixDismRepair, Invoke-VNPCfixChkdskScan, Invoke-VNPCfixChkdskFix