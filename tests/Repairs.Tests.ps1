Import-Module (Join-Path $PSScriptRoot '..\src\VNPCfix.psd1') -Force

Describe 'Repairs commands (WhatIf)' {
  It 'SFC supports ShouldProcess and does not throw with -WhatIf' {
    $threw = $false
    try { Invoke-VNPCfixSfcRepair -WhatIf } catch { $threw = $true }
    $threw | Should Be $false
  }
  It 'DISM supports ShouldProcess and does not throw with -WhatIf' {
    $threw = $false
    try { Invoke-VNPCfixDismRepair -WhatIf } catch { $threw = $true }
    $threw | Should Be $false
  }
}