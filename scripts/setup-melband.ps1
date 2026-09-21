param([string]$RuntimeRoot = (Join-Path $PSScriptRoot '../.runtime'))
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'runtime-lock.ps1')
Invoke-WithRuntimeLock -RuntimeRoot $RuntimeRoot -Action {
  $melbandHome = Join-Path ([IO.Path]::GetFullPath($RuntimeRoot)) 'melband'
  $melbandPython = Join-Path $melbandHome 'venv/Scripts/python.exe'
  if (-not (Test-Path -LiteralPath $melbandPython)) {
    & uv venv (Join-Path $melbandHome 'venv') --python 3.11
    if ($LASTEXITCODE -ne 0) { throw 'Mel-Band環境を作成できませんでした。' }
  }
  & uv pip install --python $melbandPython -r (Join-Path $PSScriptRoot '../analysis/melband-requirements.lock.txt') --extra-index-url https://download.pytorch.org/whl/cu128
  if ($LASTEXITCODE -ne 0) { throw 'Mel-Band依存を導入できませんでした。' }
  & $melbandPython (Join-Path $PSScriptRoot '../analysis/melband_install.py') $melbandHome
  if ($LASTEXITCODE -ne 0) { throw 'Mel-Bandモデルを準備できませんでした。' }
}
