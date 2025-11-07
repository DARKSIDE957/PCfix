Set-StrictMode -Version Latest

Describe 'VNPCfix Module' {
  BeforeAll {
    $moduleManifest = Join-Path $PSScriptRoot '..' | Join-Path -ChildPath 'src' | Join-Path -ChildPath 'VNPCfix.psd1'
    Import-Module $moduleManifest -Force
  }

  It 'loads the root module and nested modules' {
    (Get-Module -Name 'VNPCfix') | Should -Not -BeNullOrEmpty
  }

  It 'exports key public commands' {
    $cmds = 'Start-VNPCfix','Set-VNPCfixOptions','Invoke-VNPCfixDiagnostics','Invoke-VNPCfixSfcRepair','Invoke-VNPCfixDismRepair',
            'Invoke-VNPCfixFlushDnsAndRenewIp','Invoke-VNPCfixResetFirewall','Invoke-VNPCfixResetWindowsStoreCache',
            'Invoke-VNPCfixRebuildSearchIndex','Invoke-VNPCfixResyncTimeService'
    foreach ($c in $cmds) { (Get-Command -Name $c -ErrorAction SilentlyContinue) | Should -Not -BeNullOrEmpty }
  }

  It 'runs diagnostics in quick mode and returns a summary object' {
    $res = Invoke-VNPCfixDiagnostics
    $res | Should -Not -BeNullOrEmpty
    $res.SystemInfo | Should -Not -BeNullOrEmpty
    $res.Services   | Should -Not -BeNullOrEmpty
    $res.Network    | Should -Not -BeNullOrEmpty
    $res.Storage    | Should -Not -BeNullOrEmpty
  }
}