Set-StrictMode -Version Latest

function Show-ProgressLoop([string]$Title,[scriptblock]$Action) {
  Write-Title $Title
  try { & $Action } catch { throw }
  Write-Separator
}

function Invoke-VNPCfixSfcRepair {
  [CmdletBinding(SupportsShouldProcess)] param([switch]$Offline)
  try {
    if ($PSCmdlet.ShouldProcess('System File Checker','sfc /scannow')) {
      Show-ProgressLoop 'SFC Repair' { sfc /scannow }
      Write-Status Success 'SFC completed.'
      Write-Log -Message 'SFC repair completed' -Level INFO
    }
  } catch {
    Write-Status Error "SFC failed: $($_.Exception.Message)"
    Write-Log -Message "SFC failed: $($_.Exception.Message)" -Level ERROR
    throw
  }
}

function Invoke-VNPCfixDismRepair {
  [CmdletBinding(SupportsShouldProcess)] param()
  try {
    if ($PSCmdlet.ShouldProcess('Deployment Image Servicing and Management','DISM /Online /Cleanup-Image /RestoreHealth')) {
      Show-ProgressLoop 'DISM Repair' { DISM /Online /Cleanup-Image /RestoreHealth }
      Write-Status Success 'DISM completed.'
      Write-Log -Message 'DISM repair completed' -Level INFO
    }
  } catch {
    Write-Status Error "DISM failed: $($_.Exception.Message)"
    Write-Log -Message "DISM failed: $($_.Exception.Message)" -Level ERROR
    throw
  }
}

function Invoke-VNPCfixChkdskScan {
  [CmdletBinding(SupportsShouldProcess)] param([string]$Drive='C:')
  try {
    if ($PSCmdlet.ShouldProcess("CHKDSK scan on $Drive",'chkdsk /scan')) {
      Show-ProgressLoop "CHKDSK Scan ($Drive)" { chkdsk $Drive /scan }
      Write-Status Success 'CHKDSK scan completed.'
      Write-Log -Message "CHKDSK scan on $Drive completed" -Level INFO
    }
  } catch {
    Write-Status Error "CHKDSK scan failed: $($_.Exception.Message)"
    Write-Log -Message "CHKDSK scan failed: $($_.Exception.Message)" -Level ERROR
    throw
  }
}

function Invoke-VNPCfixChkdskFix {
  [CmdletBinding(SupportsShouldProcess,ConfirmImpact='High')]
  param([string]$Drive='C:')
  try {
    if ($PSCmdlet.ShouldProcess("CHKDSK fix on $Drive",'chkdsk /f')) {
      Show-ProgressLoop "CHKDSK Fix ($Drive)" { chkdsk $Drive /f }
      Write-Status Success 'CHKDSK fix completed.'
      Write-Log -Message "CHKDSK fix on $Drive completed" -Level INFO
    }
  } catch {
    Write-Status Error "CHKDSK fix failed: $($_.Exception.Message)"
    Write-Log -Message "CHKDSK fix failed: $($_.Exception.Message)" -Level ERROR
    throw
  }
}

function Invoke-VNPCfixWinsockReset {
  [CmdletBinding(SupportsShouldProcess,ConfirmImpact='High')]
  param()
  try {
    if ($PSCmdlet.ShouldProcess('Network Stack','netsh winsock reset; netsh int ip reset')) {
      Show-ProgressLoop 'Network Stack Reset' {
        netsh winsock reset
        netsh int ip reset
      }
      Write-Status Success 'Network stack reset. A restart may be required.'
      Write-Log -Message 'Winsock/IP stack reset executed' -Level INFO
    }
  } catch {
    Write-Status Error "Network stack reset failed: $($_.Exception.Message)"
    Write-Log -Message "Network stack reset failed: $($_.Exception.Message)" -Level ERROR
    throw
  }
}

function Invoke-VNPCfixWindowsUpdateReset {
  [CmdletBinding(SupportsShouldProcess,ConfirmImpact='High')]
  param()
  try {
    if ($PSCmdlet.ShouldProcess('Windows Update components','Stop services and reset caches')) {
      Show-ProgressLoop 'Windows Update Reset' {
        $services = 'wuauserv','bits','cryptsvc','msiserver'
        foreach ($s in $services) { try { Stop-Service -Name $s -Force -ErrorAction SilentlyContinue } catch {} }
        $sd = Join-Path $env:SystemRoot 'SoftwareDistribution'
        $cr = Join-Path $env:SystemRoot 'System32\\catroot2'
        $stamp = (Get-Date -Format 'yyyyMMdd-HHmmss')
        if (Test-Path -LiteralPath $sd) { Rename-Item -LiteralPath $sd -NewName ("SoftwareDistribution.old-" + $stamp) -ErrorAction SilentlyContinue }
        if (Test-Path -LiteralPath $cr) { Rename-Item -LiteralPath $cr -NewName ("catroot2.old-" + $stamp) -ErrorAction SilentlyContinue }
        foreach ($s in $services) { try { Start-Service -Name $s -ErrorAction SilentlyContinue } catch {} }
      }
      Write-Status Success 'Windows Update components reset.'
      Write-Log -Message 'Windows Update reset completed' -Level INFO
    }
  } catch {
    Write-Status Error "Windows Update reset failed: $($_.Exception.Message)"
    Write-Log -Message "Windows Update reset failed: $($_.Exception.Message)" -Level ERROR
    throw
  }
}

function Invoke-VNPCfixStartComponentCleanup {
  [CmdletBinding(SupportsShouldProcess)]
  param()
  try {
    if ($PSCmdlet.ShouldProcess('Component Cleanup','DISM /Online /Cleanup-Image /StartComponentCleanup')) {
      Show-ProgressLoop 'Component Cleanup' { DISM /Online /Cleanup-Image /StartComponentCleanup }
      Write-Status Success 'Component cleanup completed.'
      Write-Log -Message 'DISM StartComponentCleanup completed' -Level INFO
    }
  } catch {
    Write-Status Error "Component cleanup failed: $($_.Exception.Message)"
    Write-Log -Message "Component cleanup failed: $($_.Exception.Message)" -Level ERROR
    throw
  }
}

function Invoke-VNPCfixClearTempFiles {
  [CmdletBinding(SupportsShouldProcess)]
  param()
  try {
    if ($PSCmdlet.ShouldProcess('Clear TEMP folders','Remove-Item')) {
      Show-ProgressLoop 'Clear TEMP Folders' {
        $paths = @($env:TEMP, 'C:\\Windows\\Temp')
        foreach ($p in $paths) {
          if ($p -and (Test-Path -LiteralPath $p)) {
            Get-ChildItem -LiteralPath $p -Force -ErrorAction SilentlyContinue | ForEach-Object {
              try { Remove-Item -LiteralPath $_.FullName -Force -Recurse -ErrorAction SilentlyContinue } catch {}
            }
          }
        }
      }
      Write-Status Success 'TEMP folders cleared.'
      Write-Log -Message 'TEMP cleanup completed' -Level INFO
    }
  } catch {
    Write-Status Error "TEMP cleanup failed: $($_.Exception.Message)"
    Write-Log -Message "TEMP cleanup failed: $($_.Exception.Message)" -Level ERROR
    throw
  }
}

function Invoke-VNPCfixRegistryRepair {
  [CmdletBinding(SupportsShouldProcess)]
  param()
  try {
    if ($PSCmdlet.ShouldProcess('Windows Installer','Re-register MSI service and backup registry')) {
      $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
      $backupPath = Join-Path $env:LOCALAPPDATA (Join-Path 'PCfix' ("registry-backup-Installer-" + $stamp + '.reg'))
      Write-Status Info 'Backing up Windows Installer registry key...'
      try { & reg.exe export 'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer' "$backupPath" /y | Out-Null; Write-Log -Message "Exported Installer key to $backupPath" -Level INFO } catch { Write-Log -Message "Registry export failed: $($_.Exception.Message)" -Level WARN }
      Show-ProgressLoop 'Windows Installer re-register' {
        msiexec.exe /unregister | Out-Null
        msiexec.exe /regserver  | Out-Null
      }
      Write-Status Success 'Windows Installer re-registered.'
      Write-Log -Message 'Windows Installer re-registered' -Level INFO
    }
  } catch {
    Write-Status Error "Registry repair failed: $($_.Exception.Message)"
    Write-Log -Message "Registry repair failed: $($_.Exception.Message)" -Level ERROR
    throw
  }
}

function Invoke-VNPCfixCreateRestorePoint {
  [CmdletBinding(SupportsShouldProcess)]
  param([string]$Description = ("PCfix Restore Point " + (Get-Date -Format 'yyyyMMdd-HHmmss')))
  try {
    if ($PSCmdlet.ShouldProcess('System Restore','Create restore point')) {
      Write-Status Info "Creating system restore point: $Description"
      Checkpoint-Computer -Description $Description -RestorePointType 'MODIFY_SETTINGS'
      Write-Status Success 'Restore point created.'
      Write-Log -Message "Restore point created: $Description" -Level INFO
    }
  } catch {
    Write-Status Error 'Restore point creation failed or is disabled.'
    Write-Log -Message "Restore point failed: $($_.Exception.Message)" -Level ERROR
    throw
  }
}

function Invoke-VNPCfixWindowsUpdateCacheRestore {
  [CmdletBinding(SupportsShouldProcess)]
  param()
  try {
    if ($PSCmdlet.ShouldProcess('Windows Update cache','Restore renamed folder')) {
      $bak = Get-ChildItem (Join-Path $env:SystemRoot '.') -Filter 'SoftwareDistribution.old-*' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
      if ($bak) {
        try { Rename-Item -LiteralPath $bak.FullName -NewName 'SoftwareDistribution' -Force; Write-Status Success 'Windows Update cache restored.'; Write-Log -Message "Restored WU cache from $($bak.Name)" -Level INFO } catch { Write-Log -Message "WU cache restore failed: $($_.Exception.Message)" -Level ERROR; Write-Status Error 'Windows Update cache restore failed.' }
      } else { Write-Status Warning 'No Windows Update cache backup found.' }
    }
  } catch {
    Write-Status Error "WU cache restore failed: $($_.Exception.Message)"
    Write-Log -Message "WU cache restore failed: $($_.Exception.Message)" -Level ERROR
    throw
  }
}

Export-ModuleMember -Function Invoke-VNPCfixSfcRepair, Invoke-VNPCfixDismRepair, Invoke-VNPCfixChkdskScan, Invoke-VNPCfixChkdskFix, Invoke-VNPCfixWinsockReset, Invoke-VNPCfixWindowsUpdateReset, Invoke-VNPCfixStartComponentCleanup, Invoke-VNPCfixClearTempFiles, Invoke-VNPCfixRegistryRepair, Invoke-VNPCfixCreateRestorePoint, Invoke-VNPCfixWindowsUpdateCacheRestore