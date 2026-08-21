$ErrorActionPreference = 'Stop'

$shortcutPath = Join-Path ([Environment]::GetFolderPath('Startup')) 'VoiceBot.lnk'
if (Test-Path -LiteralPath $shortcutPath) {
    Remove-Item -LiteralPath $shortcutPath
    Write-Host "Removed startup shortcut: $shortcutPath"
} else {
    Write-Host 'VoiceBot startup shortcut was not installed.'
}
