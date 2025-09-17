#!/usr/bin/env python3
"""
MCP Server Launcher for Magic Trick Analyzer

This script launches the MCP server inside the Docker container.
It can be used as an alternative to direct docker exec commands.
"""

import subprocess
import sys
import os

def main():
    """Launch the MCP server in the Docker container"""
    try:
        # Check if the container is running
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=magic-trick-analyzer-mcp", "--format", "{{.Status}}"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if not result.stdout.strip():
            print("Error: magic-trick-analyzer-mcp container is not running", file=sys.stderr)
            print("Please start it with: docker-compose up -d", file=sys.stderr)
            sys.exit(1)
            
        if "Up" not in result.stdout:
            print(f"Error: magic-trick-analyzer-mcp container status: {result.stdout.strip()}", file=sys.stderr)
            sys.exit(1)
        
        # Launch the MCP server
        cmd = [
            "docker", "exec", "-i", 
            "magic-trick-analyzer-mcp", 
            "python", "magic_trick_mcp_server.py"
        ]
        
        # Execute the command, forwarding stdin/stdout
        process = subprocess.Popen(
            cmd,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        
        # Wait for the process to complete
        process.wait()
        sys.exit(process.returncode)
        
    except subprocess.CalledProcessError as e:
        print(f"Error running docker command: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("MCP server stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()