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
    if ($PSCmdlet.ShouldProcess("CHKDSK scan on $Drive",'chkdsk')) {
      Show-ProgressLoop "CHKDSK Scan ($Drive)" { chkdsk $Drive }
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

Export-ModuleMember -Function Invoke-VNPCfixSfcRepair, Invoke-VNPCfixDismRepair, Invoke-VNPCfixChkdskScan, Invoke-VNPCfixChkdskFix, Invoke-VNPCfixWinsockReset, Invoke-VNPCfixWindowsUpdateReset, Invoke-VNPCfixStartComponentCleanup, Invoke-VNPCfixClearTempFiles