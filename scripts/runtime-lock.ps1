function Invoke-WithRuntimeLock {
  param([string]$RuntimeRoot, [scriptblock]$Action)
  $control = Join-Path $RuntimeRoot 'control'
  New-Item -ItemType Directory -Force -Path $control | Out-Null
  $stream = [IO.File]::Open((Join-Path $control 'analysis.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::ReadWrite)
  $locked = $false
  try {
    if ($stream.Length -eq 0) { $stream.SetLength(1) }
    $stream.Lock(0, 1)
    $locked = $true
    & $Action
  } finally {
    if ($locked) { $stream.Unlock(0, 1) }
    $stream.Dispose()
  }
}
