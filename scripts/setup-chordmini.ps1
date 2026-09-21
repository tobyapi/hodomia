param([string]$RuntimeRoot = (Join-Path $PSScriptRoot '../.runtime'), [switch]$RuntimeLockHeld)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'runtime-lock.ps1')
$install = {
$chordHome = Join-Path ([IO.Path]::GetFullPath($RuntimeRoot)) 'chordmini'
$chordRepo = Join-Path $chordHome 'repo'
$chordPython = Join-Path $chordHome 'venv/Scripts/python.exe'
$commit = 'aa6e3a8d7b017f082fd2aaff9329d5c26af49c03'
New-Item -ItemType Directory -Force -Path $chordHome | Out-Null
if (-not (Test-Path -LiteralPath $chordRepo)) {
  & git clone https://github.com/ptnghia-j/ChordMini.git $chordRepo
  if ($LASTEXITCODE -ne 0) { throw 'ChordMini clone failed.' }
  & git -C $chordRepo checkout --detach $commit
  if ($LASTEXITCODE -ne 0) { throw 'ChordMini checkout failed.' }
}
$actual = & git -C $chordRepo rev-parse HEAD
if ($LASTEXITCODE -ne 0 -or $actual -ne $commit) { throw 'Unexpected ChordMini revision. Existing files were not overwritten.' }
if (-not (Test-Path -LiteralPath $chordPython)) {
  & uv venv (Join-Path $chordHome 'venv') --python 3.11
  if ($LASTEXITCODE -ne 0) { throw 'ChordMini Python environment creation failed.' }
}
& uv pip install --python $chordPython -r (Join-Path $chordRepo 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'ChordMini package installation failed.' }
& $chordPython (Join-Path $PSScriptRoot '../analysis/chordmini_install.py') $chordHome
if ($LASTEXITCODE -ne 0) { throw 'ChordMini verification failed.' }
& uv pip freeze --python $chordPython | Set-Content -Encoding utf8 (Join-Path $chordHome 'requirements.lock.txt')
Write-Output 'ChordMini setup complete. Inference runs offline.'
}
if ($RuntimeLockHeld) { & $install } else { Invoke-WithRuntimeLock -RuntimeRoot $RuntimeRoot -Action $install }
