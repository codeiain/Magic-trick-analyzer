#!/bin/bash
# Test script for MCP server

echo "Testing Magic Trick Analyzer MCP Server..."

# Test the MCP server with proper initialization sequence
(
  echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}'
  echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
  echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_stats","arguments":{}}}'
) | docker exec -i magic-trick-analyzer-mcp python magic_trick_mcp_server.py