$ErrorActionPreference = 'Stop'

$projectDirectory = $PSScriptRoot
$outputDirectory = Join-Path $projectDirectory 'build'
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$speechAssembly = Get-ChildItem (Join-Path $env:WINDIR 'Microsoft.NET\assembly\GAC_MSIL\System.Speech') -Recurse -Filter 'System.Speech.dll' | Select-Object -First 1 -ExpandProperty FullName

if (-not (Test-Path -LiteralPath $compiler)) {
    throw 'The 64-bit .NET Framework C# compiler was not found.'
}
if (-not $speechAssembly) {
    throw 'Windows System.Speech is not installed.'
}

New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
& $compiler /nologo /optimize+ /target:winexe /platform:x64 /out:"$outputDirectory\VoiceBot.exe" /reference:"$speechAssembly" /reference:System.Windows.Forms.dll /reference:System.Drawing.dll "$projectDirectory\VoiceBot.cs" "$projectDirectory\StatusOverlay.cs"
if ($LASTEXITCODE -ne 0) {
    throw "Compilation failed with exit code $LASTEXITCODE."
}

Copy-Item -LiteralPath (Join-Path $projectDirectory 'voicebot.ini') -Destination (Join-Path $outputDirectory 'voicebot.ini') -Force
Write-Host "Built $outputDirectory\VoiceBot.exe"
