param([string]$RuntimeRoot = (Join-Path $PSScriptRoot '../.runtime'))
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'runtime-lock.ps1')
Invoke-WithRuntimeLock -RuntimeRoot $RuntimeRoot -Action {
  $yamnetHome = Join-Path ([IO.Path]::GetFullPath($RuntimeRoot)) 'yamnet'
  $yamnetPython = Join-Path $yamnetHome 'venv/Scripts/python.exe'
  if (-not (Test-Path -LiteralPath $yamnetPython)) {
    & uv venv (Join-Path $yamnetHome 'venv') --python 3.11
    if ($LASTEXITCODE -ne 0) { throw 'YAMNet環境を作成できませんでした。' }
  }
  & uv pip install --python $yamnetPython -r (Join-Path $PSScriptRoot '../analysis/yamnet-requirements.lock.txt')
  if ($LASTEXITCODE -ne 0) { throw 'YAMNet依存パッケージを導入できませんでした。' }
  & $yamnetPython (Join-Path $PSScriptRoot '../analysis/yamnet_install.py') $yamnetHome
  if ($LASTEXITCODE -ne 0) { throw 'YAMNetモデルを準備できませんでした。' }
}
