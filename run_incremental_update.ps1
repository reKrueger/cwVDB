# cwVDB Incremental Update Script
# This script runs incremental updates of the vector database
# Schedule this with Windows Task Scheduler to run daily

# Set working directory to script location
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptPath

# Log file
$LogFile = "logs\incremental_update_$(Get-Date -Format 'yyyyMMdd').log"

# Start logging
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content $LogFile "[$Timestamp] Starting incremental update"

# Activate virtual environment
& "venv\Scripts\Activate.ps1"

# Run incremental indexing
Write-Host "Running incremental update..."
$Output = & python indexer.py --incremental 2>&1

# Log output
Add-Content $LogFile $Output

# Check if successful
if ($LASTEXITCODE -eq 0) {
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content $LogFile "[$Timestamp] Incremental update completed successfully"
    Write-Host "Update completed successfully"
    exit 0
} else {
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content $LogFile "[$Timestamp] ERROR: Incremental update failed with exit code $LASTEXITCODE"
    Write-Host "Update failed with exit code $LASTEXITCODE"
    exit 1
}
