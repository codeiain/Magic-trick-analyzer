@echo off
REM Magic Trick Analyzer MCP Server Launcher for Windows
REM This batch file launches the MCP server in the Docker container

echo Starting Magic Trick Analyzer MCP Server...

REM Check if container is running
docker ps --filter "name=magic-trick-analyzer-mcp" --format "{{.Status}}" > temp_status.txt
set /p CONTAINER_STATUS=<temp_status.txt
del temp_status.txt

if "%CONTAINER_STATUS%"=="" (
    echo Error: magic-trick-analyzer-mcp container is not running
    echo Please start it with: docker-compose up -d
    exit /b 1
)

echo Container Status: %CONTAINER_STATUS%
echo Launching MCP server...

REM Launch the MCP server
docker exec -i magic-trick-analyzer-mcp python magic_trick_mcp_server.py