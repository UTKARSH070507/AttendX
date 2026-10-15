#!/usr/bin/env python3
"""
AttendX - Frontend Preview Server (Phase 2)
Lightweight HTTP server using Python standard library to preview the frontend dashboard.
"""
import http.server
import socketserver
import sys

PORT = 5000

class AttendXPreviewHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self.path = '/templates/index.html'
        return super().do_GET()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), AttendXPreviewHandler) as httpd:
        print(f"==================================================")
        print(f" AttendX Frontend Preview Server Running")
        print(f" URL: http://localhost:{port}")
        print(f" Press Ctrl+C to stop the server.")
        print(f"==================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nPreview server stopped.")

