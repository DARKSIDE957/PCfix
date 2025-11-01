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

Export-ModuleMember -Function Invoke-VNPCfixSfcRepair, Invoke-VNPCfixDismRepair, Invoke-VNPCfixChkdskScan, Invoke-VNPCfixChkdskFix