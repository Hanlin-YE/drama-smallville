$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Backend = Join-Path $Root "script simulation\backend"
$Frontend = Join-Path $Root "script simulation\frontend"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$Url = "http://127.0.0.1:5173"

function Get-CommandPath($name) {
  $command = Get-Command $name -ErrorAction SilentlyContinue
  if ($command) {
    return $command.Source
  }
  return $null
}

function Test-HttpOk($url) {
  try {
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
    return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
  } catch {
    return $false
  }
}

function Wait-Http($url, $seconds) {
  $deadline = (Get-Date).AddSeconds($seconds)
  while ((Get-Date) -lt $deadline) {
    if (Test-HttpOk $url) {
      return $true
    }
    Start-Sleep -Milliseconds 500
  }
  return $false
}

if (-not (Test-Path $VenvPython)) {
  $python = Get-CommandPath "python"
  if (-not $python) {
    $pyLauncher = Get-CommandPath "py"
    if (-not $pyLauncher) {
      throw "Python was not found. Install Python 3, then run this script again."
    }
    Write-Host "Creating local Python virtual environment..."
    & $pyLauncher -3 -m venv (Join-Path $Root ".venv")
  } else {
    Write-Host "Creating local Python virtual environment..."
    & $python -m venv (Join-Path $Root ".venv")
  }
}

$depsOk = $false
try {
  & $VenvPython -c "import fastapi, uvicorn, pydantic, httpx" *> $null
  $depsOk = $LASTEXITCODE -eq 0
} catch {
  $depsOk = $false
}

if (-not $depsOk) {
  Write-Host "Installing backend dependencies..."
  & $VenvPython -m pip install -r (Join-Path $Backend "requirements.txt")
  if ($LASTEXITCODE -ne 0) {
    throw "Backend dependency installation failed."
  }
}

if (-not (Test-HttpOk "http://127.0.0.1:8000/health")) {
  Write-Host "Starting backend on http://127.0.0.1:8000 ..."
  Start-Process -FilePath $VenvPython `
    -ArgumentList @("-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000") `
    -WorkingDirectory $Backend `
    -WindowStyle Hidden
}

$node = Get-CommandPath "node"
if (-not $node) {
  throw "Node.js was not found. Install Node.js, then run this script again."
}

$viteJs = Join-Path $Frontend "node_modules\vite\bin\vite.js"
$rollupNative = Join-Path $Frontend "node_modules\@rollup\rollup-win32-x64-msvc"
if ((-not (Test-Path $viteJs)) -or (-not (Test-Path $rollupNative))) {
  $npm = Get-CommandPath "npm.cmd"
  if (-not $npm) {
    $npm = Get-CommandPath "npm"
  }
  if (-not $npm) {
    throw "Frontend dependencies are missing and npm was not found."
  }
  Write-Host "Installing frontend dependencies..."
  & $npm install --prefix $Frontend
  if ($LASTEXITCODE -ne 0) {
    throw "Frontend dependency installation failed."
  }
}

if (-not (Test-HttpOk $Url)) {
  Write-Host "Starting frontend on $Url ..."
  Start-Process -FilePath $node `
    -ArgumentList @("`"$viteJs`"", "--host", "127.0.0.1", "--port", "5173") `
    -WorkingDirectory $Frontend `
    -WindowStyle Hidden
}

Write-Host "Waiting for project URL..."
if (-not (Wait-Http $Url 25)) {
  Write-Warning "The frontend did not respond yet. Opening the URL anyway."
}

Start-Process $Url
Write-Host "Opened $Url"
