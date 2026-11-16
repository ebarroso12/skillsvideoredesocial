# Instala a skill video-caricatura-social no Windows (Claude Code, Codex ou pasta personalizada).
# Uso:  .\install.ps1            (Claude Code)   |  .\install.ps1 -Target codex  |  .\install.ps1 -Dest "C:\pasta"
param([ValidateSet("claude","codex","agents","all")][string]$Target = "claude", [string]$Dest = "")
$ErrorActionPreference = "Stop"
$Skill = "video-caricatura-social"
$Src = Join-Path $PSScriptRoot "skills\$Skill"
if (-not (Test-Path (Join-Path $Src "SKILL.md"))) { throw "SKILL.md nao encontrado em $Src" }
$home_ = $env:USERPROFILE
$targets = @()
if ($Dest) { $targets += $Dest } else {
  switch ($Target) {
    "claude" { $targets += "$home_\.claude\skills" }
    "codex"  { $targets += "$home_\.codex\skills" }
    "agents" { $targets += "$home_\.agents\skills" }
    "all"    { $targets += "$home_\.claude\skills","$home_\.codex\skills","$home_\.agents\skills" }
  }
}
foreach ($t in $targets) {
  New-Item -ItemType Directory -Force -Path $t | Out-Null
  $d = Join-Path $t $Skill
  if (Test-Path $d) { Remove-Item -Recurse -Force $d }
  Copy-Item -Recurse $Src $d
  Write-Host "Instalada em: $d"
}
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { Write-Host "FALTA: ffmpeg (https://ffmpeg.org/download.html)" }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { Write-Host "FALTA: python 3" } else { python -c "import PIL" 2>$null; if ($LASTEXITCODE -ne 0) { Write-Host "FALTA: Pillow -> pip install pillow" } }
