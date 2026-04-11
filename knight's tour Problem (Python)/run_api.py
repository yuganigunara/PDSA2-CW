#!/usr/bin/env python
"""Launch the Knight's Tour API server."""
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from knighttour.api import app

if __name__ == '__main__':
    print("Starting Knight's Tour API server...")
    print("Server running at http://localhost:5000/")
    print("API endpoints:")
    print("  POST /api/solve - Solve knight tour")
    print("  GET  /api/winners - Get saved winners")
    print("  POST /api/winners - Save a winner")
    print("  GET  /api/health - Health check")
    app.run(debug=True, host='0.0.0.0', port=5000)
