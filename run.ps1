# Sentinel Launch Script
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  SENTINEL - Privileged Access Monitoring Tool (T2-PS4)  " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$backendDir = Join-Path $PSScriptRoot "backend"
$pythonExe = "C:\Users\kavin raja m\AppData\Local\Programs\Python\Python312\python.exe"

if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

Write-Host "`nStarting Sentinel backend server on http://localhost:8000 ..." -ForegroundColor Green
Start-Process -FilePath $pythonExe -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8000" -WorkingDirectory $backendDir

Start-Sleep -Seconds 3

Write-Host "Launching Google Chrome at http://localhost:8000 ..." -ForegroundColor Yellow
Start-Process "http://localhost:8000"

Write-Host "`nSentinel is running! Press Ctrl+C in the server window to stop.`n" -ForegroundColor Green
