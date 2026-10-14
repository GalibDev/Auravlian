$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$installTarget = [IO.Path]::GetFullPath((Join-Path $workspace 'artifacts\installed-smoke'))
if (-not $installTarget.StartsWith($workspace + '\')) { throw 'Test install must stay inside workspace' }
$uninstallKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{7C160C8E-0EC3-4F53-AB24-605BAF10BBA2}_is1'
if (Test-Path $uninstallKey) { throw 'An existing Auravlian installation is registered; use a separate VM for this test.' }
$setup = Start-Process -FilePath (Join-Path $workspace 'dist\Auravlian-Setup-0.8.0.exe') -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',"/DIR=$installTarget",'/GROUP="Auravlian Test Install"','/TASKS=' -WindowStyle Hidden -PassThru
if (-not $setup.WaitForExit(30000) -or $setup.ExitCode -ne 0) { throw 'Installer did not complete successfully' }
$diagnostics = Join-Path $workspace 'artifacts\installed-runtime-smoke'
$diagnosticStart = Get-Date
$appTest = Start-Process -FilePath (Join-Path $installTarget 'Auravlian.exe') -ArgumentList '--smoke-test',$diagnostics -WindowStyle Hidden -PassThru
if (-not $appTest.WaitForExit(30000)) { Stop-Process -Id $appTest.Id; throw 'Installed app smoke timed out' }
if ($appTest.ExitCode -ne 0) { throw 'Installed app exited with an error' }
if ((Get-Item (Join-Path $diagnostics 'result.json')).LastWriteTime -lt $diagnosticStart) { throw 'Diagnostic result was not refreshed by this run' }
$result = Get-Content (Join-Path $diagnostics 'result.json') -Raw | ConvertFrom-Json
if ($result.result -ne 'passed') { throw 'Installed runtime diagnostic failed' }
$shortcut = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Auravlian Test Install\Auravlian.lnk'
if (-not (Test-Path $shortcut)) { throw 'Start Menu shortcut was not created' }
$uninstallPath = [IO.Path]::GetFullPath((Join-Path $installTarget 'unins000.exe'))
if (-not $uninstallPath.StartsWith($workspace + '\')) { throw 'Unsafe uninstall target' }
$uninstall = Start-Process -FilePath $uninstallPath -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART' -WindowStyle Hidden -PassThru
if (-not $uninstall.WaitForExit(30000) -or $uninstall.ExitCode -ne 0) { throw 'Uninstall failed' }
if ((Test-Path (Join-Path $installTarget 'Auravlian.exe')) -or (Test-Path $shortcut)) { throw 'Installed files/shortcut remain' }
$report = @{ installer_exit = $setup.ExitCode; runtime_result = $result; start_menu_verified = $true; uninstall_exit = $uninstall.ExitCode; installed_exe_removed = $true; diagnostic_database_preserved = (Test-Path (Join-Path $diagnostics 'library\library.sqlite3')); clean_vm = $false }
$report | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $workspace 'artifacts\installer-verification.json')
$report | ConvertTo-Json -Depth 4
