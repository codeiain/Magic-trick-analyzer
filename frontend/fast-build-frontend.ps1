#!/usr/bin/env pwsh

# Magic Trick Analyzer Frontend - Fast Build Script

Write-Host "Building Magic Trick Analyzer Frontend..." -ForegroundColor Magenta

# Set error handling
$ErrorActionPreference = "Stop"

try {
    # Navigate to frontend directory
    Set-Location "c:\docker\magic-trick-analyzer\frontend"
    
    # Build only the frontend service
    Write-Host "Building frontend Docker image..." -ForegroundColor Yellow
    docker build -t magic-trick-analyzer-frontend:latest .
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Frontend build completed successfully!" -ForegroundColor Green
        
        # Option to run the service
        $runNow = Read-Host "Would you like to start the frontend service? (y/N)"
        if ($runNow -eq "y" -or $runNow -eq "Y") {
            Write-Host "Starting Magic Trick Analyzer services..." -ForegroundColor Cyan
            Set-Location "c:\docker\magic-trick-analyzer"
            docker-compose up -d
            
            Write-Host "Services started! Access the frontend at: http://localhost:3000" -ForegroundColor Green
            Write-Host "API available at: http://localhost:8084" -ForegroundColor Green
        }
    } else {
        Write-Host "Frontend build failed!" -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Host "Build failed with error: $_" -ForegroundColor Red
    exit 1
} finally {
    # Return to original directory
    Set-Location "c:\docker"
}

Write-Host "Frontend build process complete!" -ForegroundColor Magenta
