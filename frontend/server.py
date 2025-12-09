#!/usr/bin/env python3
"""
Simple HTTP Server with No-Cache Headers for Development
Prevents browser caching during active development
"""

import http.server
import socketserver
from datetime import datetime

PORT = 5500

class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with no-cache headers"""
    
    def end_headers(self):
        # Add no-cache headers to prevent browser caching
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def log_message(self, format, *args):
        # Custom log format with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {self.address_string()} - {format % args}")

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), NoCacheHTTPRequestHandler) as httpd:
        print(f"✅ Development server running on http://localhost:{PORT}")
        print(f"📁 Serving files from: {httpd.server_address}")
        print(f"🔄 Cache disabled - files will always refresh")
        print(f"\n🌐 Open: http://localhost:{PORT}/index.html")
        print(f"⏹️  Press Ctrl+C to stop\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n⏹️  Server stopped")
