$ErrorActionPreference = 'Stop'

$executable = Join-Path $PSScriptRoot 'build\VoiceBot.exe'
if (-not (Test-Path -LiteralPath $executable)) {
    throw 'VoiceBot.exe was not found. Run .\build.ps1 first.'
}

$startupDirectory = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupDirectory 'VoiceBot.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $executable
$shortcut.WorkingDirectory = Split-Path -Parent $executable
$shortcut.Description = 'Offline VoiceBot wake-word listener'
$shortcut.WindowStyle = 7
$shortcut.Save()

Write-Host "Startup shortcut installed: $shortcutPath"
Write-Host 'VoiceBot will start automatically the next time you sign in.'
