param([string]$RuntimeRoot = (Join-Path $PSScriptRoot '../.runtime'))
$ErrorActionPreference = 'Stop'
$RuntimeRoot = [IO.Path]::GetFullPath($RuntimeRoot)
$sourceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
New-Item -ItemType Directory -Force -Path $RuntimeRoot | Out-Null
$python = Join-Path $RuntimeRoot 'venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) {
  & uv venv (Join-Path $RuntimeRoot 'venv') --python 3.11
  if ($LASTEXITCODE -ne 0) { throw 'Python 環境の作成に失敗しました。uv が必要です。' }
}
& uv pip install --python $python -r (Join-Path $sourceRoot 'analysis/requirements.lock.txt') --extra-index-url https://download.pytorch.org/whl/cu128 --index-strategy unsafe-best-match
if ($LASTEXITCODE -ne 0) { throw '解析パッケージのインストールに失敗しました。' }
& $python (Join-Path $sourceRoot 'analysis/prepare.py') --runtime $RuntimeRoot
if ($LASTEXITCODE -ne 0) { throw 'モデルのセットアップに失敗しました。ログを確認して再実行してください。' }
& uv pip freeze --python $python | Set-Content -Encoding utf8 (Join-Path $RuntimeRoot 'requirements.lock.txt')
Write-Output '解析環境の準備が完了しました。'
