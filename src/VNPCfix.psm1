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
          $pcfixPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'PCfix.ps1'
          if (Request-Elevation -ScriptPath $pcfixPath -Args '') { break }
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
        Format-MenuItem 17 'Update Everything (Windows + Defender)'
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
          '17' { try { Invoke-VNPCfixUpdateAll -WhatIf:$whatIfSwitch } catch {} }
          '0'  { Write-Status Info 'Returning to main menu.' }
          default { Write-Status Warning 'Invalid selection.' }
        }
      }
      '0' { Write-Status Info 'Goodbye.'; return }
      default { Write-Status Warning 'Invalid selection.' }
    }
  }
}

function Invoke-VNPCfixUpdateAll {
  [CmdletBinding(SupportsShouldProcess,ConfirmImpact='High')]
  param()
  try {
    Write-Title 'Update Everything'
    if ($PSCmdlet.ShouldProcess('Windows Update','Scan, download, and install available updates')) {
      Write-Status Info 'Triggering Windows Update scan...'
      try {
        $uso = (Get-Command UsoClient.exe -ErrorAction SilentlyContinue)
        if ($uso) {
          Show-ProgressLoop -Title 'Windows Update Scan' -Action { UsoClient.exe StartScan }
          Write-Status Info 'Starting update download...'
          Show-ProgressLoop -Title 'Windows Update Download' -Action { UsoClient.exe StartDownload }
          Write-Status Info 'Starting update install...'
          Show-ProgressLoop -Title 'Windows Update Install' -Action { UsoClient.exe StartInstall }
        } else {
          Show-ProgressLoop -Title 'Windows Update Scan' -Action { wuauclt /detectnow }
          Show-ProgressLoop -Title 'Windows Update Install' -Action { wuauclt /updatenow }
        }
        Write-Log -Message 'Windows Update scan/download/install triggered' -Level INFO
        Write-Status Success 'Windows Update actions triggered.'
      } catch {
        Write-Status Warning "Windows Update trigger failed: $($_.Exception.Message)"
        Write-Log -Message "Windows Update trigger failed: $($_.Exception.Message)" -Level WARN
      }
    }

    if ($PSCmdlet.ShouldProcess('Microsoft Defender','Update signatures')) {
      Write-Status Info 'Updating Microsoft Defender signatures...'
      try { Update-MpSignature -ErrorAction Stop; Write-Log -Message 'Defender signatures updated' -Level INFO; Write-Status Success 'Defender signatures updated.' } catch { Write-Status Warning "Defender signature update unavailable: $($_.Exception.Message)"; Write-Log -Message "Defender signature update failed: $($_.Exception.Message)" -Level WARN }
    }

    if ($PSCmdlet.ShouldProcess('Component Cleanup','DISM StartComponentCleanup')) {
      try { Show-ProgressLoop -Title 'Component Cleanup' -Action { DISM /Online /Cleanup-Image /StartComponentCleanup }; Write-Log -Message 'DISM StartComponentCleanup executed' -Level INFO; Write-Status Success 'Component cleanup completed.' } catch { Write-Status Warning "Component cleanup failed: $($_.Exception.Message)"; Write-Log -Message "Component cleanup failed: $($_.Exception.Message)" -Level WARN }
    }

    Write-Separator
    Write-Status Info 'Some updates may require a restart to complete.'
  } catch {
    Write-Status Error "Update Everything failed: $($_.Exception.Message)"
    Write-Log -Message "Update Everything failed: $($_.Exception.Message)" -Level ERROR
    throw
  }
}

Export-ModuleMember -Function Start-VNPCfix, Set-VNPCfixOptions, Write-Log, Invoke-VNPCfixDiagnostics, Invoke-VNPCfixSfcRepair, Invoke-VNPCfixDismRepair, Invoke-VNPCfixChkdskScan, Invoke-VNPCfixChkdskFix, Invoke-VNPCfixWinsockReset, Invoke-VNPCfixWindowsUpdateReset, Invoke-VNPCfixStartComponentCleanup, Invoke-VNPCfixClearTempFiles, Invoke-VNPCfixRegistryRepair, Invoke-VNPCfixCreateRestorePoint, Invoke-VNPCfixWindowsUpdateCacheRestore, Invoke-VNPCfixFlushDnsAndRenewIp, Invoke-VNPCfixResetFirewall, Invoke-VNPCfixResetWindowsStoreCache, Invoke-VNPCfixRebuildSearchIndex, Invoke-VNPCfixResyncTimeService, Invoke-VNPCfixUpdateAll