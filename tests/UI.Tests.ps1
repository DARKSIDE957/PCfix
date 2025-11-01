Import-Module (Join-Path $PSScriptRoot '..\src\VNPCfix.psd1') -Force

Describe 'UI helpers' {
  It 'Centers text within console width without throwing' {
    $threw = $false
    try { Center-Text 'VN PCfix' } catch { $threw = $true }
    $threw | Should Be $false
  }

  It 'Writes status lines without throwing' {
    $threw = $false
    try {
      Write-Status Info 'Test info'
      Write-Status Success 'Test success'
      Write-Status Warning 'Test warning'
      Write-Status Error 'Test error'
    } catch { $threw = $true }
    $threw | Should Be $false
  }
}