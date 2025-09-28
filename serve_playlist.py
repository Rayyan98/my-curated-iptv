#!/usr/bin/env python3

import http.server
import socketserver
import socket
import os
import sys

class PlaylistHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.getcwd(), **kwargs)
    
    def end_headers(self):
        # Add CORS headers to allow cross-origin requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        
        # Set proper content type for M3U files
        if self.path.endswith('.m3u'):
            self.send_header('Content-Type', 'application/x-mpegurl')
        
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Connect to a remote server to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except Exception:
        return "localhost"

def main():
    PORT = 8081
    
    # Check if M3U file exists
    m3u_file = "pk_working.m3u"
    if not os.path.exists(m3u_file):
        print(f"Error: {m3u_file} not found!")
        print("Please run check_playlist.py first to create the filtered playlist.")
        sys.exit(1)
    
    # Get local IP address
    local_ip = get_local_ip()
    
    # Create and start the server
    try:
        with socketserver.TCPServer(("", PORT), PlaylistHTTPRequestHandler) as httpd:
            print("=" * 60)
            print("🎬 M3U Playlist Server Started!")
            print("=" * 60)
            print(f"📁 Serving files from: {os.getcwd()}")
            print(f"🌐 Local IP: {local_ip}")
            print(f"🔗 Port: {PORT}")
            print()
            print("📺 TV/Player URLs:")
            print(f"   • Local: http://localhost:{PORT}/{m3u_file}")
            print(f"   • Network: http://{local_ip}:{PORT}/{m3u_file}")
            print()
            print("📋 Available files:")
            for file in os.listdir("."):
                if file.endswith((".m3u", ".m3u8")):
                    print(f"   • http://{local_ip}:{PORT}/{file}")
            print()
            print("🛑 Press Ctrl+C to stop the server")
            print("=" * 60)
            
            httpd.serve_forever()
            
    except PermissionError:
        print(f"Permission denied to bind to port {PORT}")
        print("Try using a different port (like 8081) or run with sudo")
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    main()