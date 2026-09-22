# Get the directory of this script (workspace root)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Talent Vellocity Backend (Hidden Background Process)
$BackendCwd = Join-Path $ScriptDir "Talent Vellocity\sces\backend"
$BackendExec = Join-Path $BackendCwd "venv\Scripts\uvicorn.exe"
Start-Process powershell -ArgumentList "-Command", "cd '$BackendCwd'; & '$BackendExec' app.main:app --port 8000 --reload" -WindowStyle Hidden

# 2. Talent Vellocity Frontend (Hidden Background Process)
$FrontendCwd = Join-Path $ScriptDir "Talent Vellocity\sces\frontend"
Start-Process powershell -ArgumentList "-Command", "cd '$FrontendCwd'; npm run dev" -WindowStyle Hidden

# 3. Capstone Interview Prep Backend (Visible Console Process for Debug Logs)
$CapstoneBackendCwd = Join-Path $ScriptDir "final-capstone-project-agentic-ai-interview-preparation-assistant"
$CapstoneBackendExec = Join-Path $ScriptDir "Talent Vellocity\sces\backend\venv\Scripts\uvicorn.exe"
Start-Process powershell -ArgumentList "-Command", "cd '$CapstoneBackendCwd'; & '$CapstoneBackendExec' api:app --port 8090 --reload"

# 4. Capstone Interview Prep Frontend (Hidden Background Process)
$CapstoneFrontendCwd = Join-Path $ScriptDir "final-capstone-project-agentic-ai-interview-preparation-assistant\frontend"
Start-Process powershell -ArgumentList "-Command", "cd '$CapstoneFrontendCwd'; npm run dev" -WindowStyle Hidden

# 5. Placement Readiness Verdict Agent (Hidden Background Process)
$VerdictCwd = Join-Path $ScriptDir "readiness-verdict-agent"
Start-Process powershell -ArgumentList "-Command", "cd '$VerdictCwd'; & '$CapstoneBackendExec' app:app --port 8002 --reload" -WindowStyle Hidden

# Output the main page link as requested by the user
Write-Host "main page : -http://localhost:5173" -ForegroundColor Green

Write-Host ""
Write-Host "All backend and frontend servers are active in the background." -ForegroundColor Cyan
Read-Host "Press [ENTER] to stop all servers and free up ports (8000, 8090, 8002, 5173, 5174)"

Write-Host "Terminating application processes..." -ForegroundColor Red
$Ports = @(8000, 8090, 8002, 5173, 5174)
foreach ($Port in $Ports) {
    $Conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    foreach ($Conn in $Conns) {
        if ($Conn.OwningProcess) {
            Stop-Process -Id $Conn.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
}
Write-Host "All servers stopped cleanly. Port release complete!" -ForegroundColor Green

