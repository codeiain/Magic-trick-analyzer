#!/usr/bin/env python3
"""
Main entry point for the Magic Trick Analyzer service.
"""
import uvicorn
from src.presentation.app import app, get_config


def main():
    """Main function to run the application."""
    config = get_config()
    
    uvicorn.run(
        "src.presentation.app:app",
        host=config.api.host,
        port=config.api.port,
        workers=config.api.workers,
        reload=config.api.reload,
        log_level=config.api.log_level,
        access_log=True
    )


if __name__ == "__main__":
    main()
