#!/usr/bin/env python3
"""
Entry point for batch importing disc images.

This script should be run from Docker or with proper Python path:
    docker exec <container> python /app/app/batch_import_discs.py /path/to/images
"""
import sys
from pathlib import Path

# Ensure the app directory is in the path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Import and run the CLI tool
from disc_identification.cli.batch_import import main

if __name__ == '__main__':
    main()
