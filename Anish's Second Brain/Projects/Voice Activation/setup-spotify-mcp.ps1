$ErrorActionPreference = 'Stop'
$server = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'spotify-mcp-server.js')).Path
$privateDirectory = Join-Path $env:USERPROFILE '.codex'
$privateConfig = Join-Path $privateDirectory 'spotify.env'
New-Item -ItemType Directory -Path $privateDirectory -Force | Out-Null
if (-not (Test-Path -LiteralPath $privateConfig)) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'spotify.env.example') -Destination $privateConfig
    Write-Host "Created $privateConfig. Edit it with your Spotify Client ID and Secret, then run this script again."
    exit 0
}

& codex mcp add voicebot-spotify -- node $server
if ($LASTEXITCODE -ne 0) { throw "Codex MCP registration failed with exit code $LASTEXITCODE." }
Write-Host 'Registered voicebot-spotify with Codex.'
Write-Host 'Restart Codex, then ask it to call spotify_auth and approve the Spotify browser window.'
