Import-Module (Join-Path $PSScriptRoot '..\src\VNPCfix.psd1') -Force

Describe 'Core state and logging' {
  It 'Initializes logging and creates a log file path' {
    Initialize-Logging
    ($script:State.LogFile -ne $null) | Should Be $true
  }

  It 'Applies UI options via Set-VNPCfixOptions' {
    Set-VNPCfixOptions -BasicASCII -HighContrast
    ($script:State.UI.BasicASCII -eq $true) | Should Be $true
    ($script:State.UI.HighContrast -eq $true) | Should Be $true
  }
}