Set-StrictMode -Version Latest

function Test-IsAdmin {
  try {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($id)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  } catch {
    return $false
  }
}

function Request-Elevation {
  param([string]$ScriptPath,[string]$Args)
  try {
    Start-Process -FilePath 'powershell.exe' -ArgumentList "-ExecutionPolicy Bypass -File `"$ScriptPath`" $Args" -Verb RunAs -Wait
    return $true
  } catch {
    Write-Warning "Elevation request failed: $($_.Exception.Message)"
    return $false
  }
}

Export-ModuleMember -Function Test-IsAdmin, Request-Elevation