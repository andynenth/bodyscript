#!/usr/bin/env python
"""
Start the BodyScript Creative Web Server
Simple launcher script for the web application
"""

import sys
import os

# Add creative directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("\n" + "="*60)
    print("🎨 BodyScript Creative Platform")
    print("="*60)
    print("\nStarting web server...")
    print("\nAccess the application at:")
    print("  Web UI: http://localhost:8000/ui")
    print("  API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")

    try:
        # Import and run the FastAPI app
        from creative.web.app import app
        import uvicorn

        # Run the server
        uvicorn.run(app, host="0.0.0.0", port=8000)

    except ImportError as e:
        print(f"\n❌ Error: Missing dependencies")
        print(f"Details: {e}")
        print("\nPlease install required packages:")
        print("  pip install fastapi uvicorn python-multipart aiofiles")
        print("\nOr install all creative requirements:")
        print("  pip install -r requirements_creative.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()