"""
Simple HTTPS Server for Hillview School Management System
Bypasses Flask app initialization issues by using a basic server
"""

import ssl
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import json
from urllib.parse import urlparse, parse_qs

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy_request()
    
    def do_POST(self):
        self.proxy_request()
    
    def do_PUT(self):
        self.proxy_request()
    
    def do_DELETE(self):
        self.proxy_request()
    
    def proxy_request(self):
        try:
            # Target Flask app
            target_url = f"http://127.0.0.1:8080{self.path}"
            
            # Get request body if present
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Forward headers
            headers = {}
            for header, value in self.headers.items():
                if header.lower() not in ['host', 'connection']:
                    headers[header] = value
            
            # Make request to Flask app
            response = requests.request(
                method=self.command,
                url=target_url,
                data=body,
                headers=headers,
                allow_redirects=False,
                timeout=30
            )
            
            # Send response back
            self.send_response(response.status_code)
            
            # Forward response headers
            for header, value in response.headers.items():
                if header.lower() not in ['connection', 'transfer-encoding']:
                    self.send_header(header, value)
            
            # Add security headers
            self.send_header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-XSS-Protection', '1; mode=block')
            
            self.end_headers()
            
            # Send response body
            if response.content:
                self.wfile.write(response.content)
                
        except requests.exceptions.ConnectionError:
            self.send_error(503, "Flask app is not running on port 8080")
        except Exception as e:
            self.send_error(500, f"Proxy error: {str(e)}")
    
    def log_message(self, format, *args):
        # Custom logging
        print(f"🌐 HTTPS Request: {format % args}")

def main():
    print("🔐 Starting HTTPS Proxy Server for Hillview School Management System")
    print("📍 Target: http://127.0.0.1:8080 (Flask app)")
    print("🌐 HTTPS Server: https://localhost:8443")
    
    # Check if SSL files exist
    if not os.path.exists('ssl/cert.pem') or not os.path.exists('ssl/key.pem'):
        print("❌ SSL certificate files not found!")
        print("   Run: ./generate_ssl.bat to create SSL certificates")
        return
    
    # Create HTTPS server
    httpd = HTTPServer(('0.0.0.0', 8443), ProxyHandler)
    
    # Configure SSL
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain('ssl/cert.pem', 'ssl/key.pem')
    
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    print("✅ HTTPS server started successfully!")
    print("🚀 Access your site at: https://localhost:8443")
    print("⚠️  Browser will show security warning - click 'Advanced' and proceed")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 HTTPS server stopped")

if __name__ == '__main__':
    main()