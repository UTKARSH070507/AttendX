#!/usr/bin/env python3
"""
AttendX - Application Runner
Starts the integrated Flask application and SQLite database backend.
"""
import os
import sys

if __name__ == '__main__':
    # Automatically use local virtualenv if available
    venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'bin', 'python')
    if os.path.exists(venv_python) and sys.executable != venv_python and 'VIRTUAL_ENV' not in os.environ:
        os.execv(venv_python, [venv_python, os.path.abspath(__file__)] + sys.argv[1:])

    from app import create_app
    from config import Config
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app = create_app(Config)
    print("==================================================")
    print(" AttendX Academic Analytics System")
    print(f" URL: http://localhost:{port}")
    print(" Database: Connected (SQLite)")
    print(" Press Ctrl+C to stop.")
    print("==================================================")
    app.run(host='0.0.0.0', port=port, debug=False)
