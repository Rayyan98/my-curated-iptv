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
    import argparse
    
    parser = argparse.ArgumentParser(description='Serve M3U playlist files over HTTP')
    parser.add_argument('-p', '--port', type=int, default=8081, help='Port to serve on (default: 8081)')
    parser.add_argument('-f', '--file', help='Specific M3U file to highlight (optional)')
    
    args = parser.parse_args()
    PORT = args.port
    
    # Find available M3U files
    m3u_files = [f for f in os.listdir(".") if f.endswith((".m3u", ".m3u8"))]
    
    if not m3u_files:
        print("Error: No M3U files found in current directory!")
        print("Please run 'make all' or check_playlist.py first to create filtered playlists.")
        sys.exit(1)
    
    # If specific file requested, check it exists
    if args.file and not os.path.exists(args.file):
        print(f"Error: Specified file '{args.file}' not found!")
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
            if args.file:
                print(f"   🎯 Featured: http://{local_ip}:{PORT}/{args.file}")
            print()
            print("📋 Available files:")
            for file in sorted(m3u_files):
                marker = "🎯 " if args.file == file else "   • "
                print(f"{marker}http://{local_ip}:{PORT}/{file}")
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