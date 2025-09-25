#!/usr/bin/env python3
"""
Simple HTTPS test server for the Hillview School Management System.
This script runs the application with HTTPS support for development/testing.
"""

import os
import sys
import ssl
from pathlib import Path

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

def _load_env_file():
    """Load environment variables from .env files."""
    candidates = [
        os.path.join(current_dir, '.env'),
        os.path.join(current_dir, '.env.development'),
        os.path.join(current_dir, '.env.local'),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for raw in f:
                        line = raw.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' not in line:
                            continue
                        key, val = line.split('=', 1)
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        # Don't override if already set in the environment
                        if key and key not in os.environ:
                            os.environ[key] = val
                break
            except Exception:
                pass

def generate_self_signed_cert():
    """Generate self-signed SSL certificate for HTTPS testing."""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime
        import ipaddress
        
        # Create SSL directory if it doesn't exist
        ssl_dir = os.path.join(current_dir, 'ssl')
        os.makedirs(ssl_dir, exist_ok=True)
        
        cert_path = os.path.join(ssl_dir, 'cert.pem')
        key_path = os.path.join(ssl_dir, 'key.pem')
        
        # Check if certificates already exist
        if os.path.exists(cert_path) and os.path.exists(key_path):
            print(f"✅ Using existing SSL certificates")
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(cert_path, key_path)
            return context
        
        print("🔐 Generating self-signed SSL certificate...")
        
        # Generate private key
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Generate certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Development"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Hillview School"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        ).sign(key, hashes.SHA256())
        
        # Write certificate and key files
        with open(cert_path, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
            
        with open(key_path, 'wb') as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print(f"✅ SSL certificate generated: {cert_path}")
        print(f"✅ Private key generated: {key_path}")
        
        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_path, key_path)
        return context
        
    except ImportError:
        print("❌ cryptography library not installed. Install with: pip install cryptography")
        return 'adhoc'  # Flask will generate adhoc SSL context
    except Exception as e:
        print(f"❌ Error generating SSL certificate: {e}")
        return 'adhoc'

def main():
    """Main function to run the HTTPS test server."""
    _load_env_file()
    
    try:
        # Configuration
        PORT = int(os.environ.get('HTTPS_PORT', 8443))
        HOST = os.environ.get('HOST', '127.0.0.1')
        
        # Set up environment for development with HTTPS
        os.environ['REDIS_DISABLED'] = '1'  # Disable Redis for testing
        
        print("🚀 Hillview School Management System - HTTPS Test Server")
        print(f"🔐 HTTPS Server starting on: https://{HOST}:{PORT}")
        print("⏳ Initializing application...")
        
        # Generate SSL certificate
        ssl_context = generate_self_signed_cert()
        
        # Import create_app from the new_structure package
        from new_structure import create_app
        
        # Create the Flask application in development mode with HTTPS
        app = create_app('development')
        
        print("✅ Application initialized successfully")
        print("🛡️ HTTPS features enabled:")
        print("  • SSL/TLS encryption")
        print("  • Security headers")
        print("  • CSRF protection")
        print("🌐 Ready to accept HTTPS connections...")
        print("")
        print("📝 Note: Browser will show security warning for self-signed certificate")
        print("   Click 'Advanced' and 'Proceed to localhost (unsafe)' to continue")
        print("")
        
        # Run the application with HTTPS
        app.run(
            host=HOST,
            port=PORT,
            debug=True,
            ssl_context=ssl_context,
            threaded=True,
            use_reloader=False
        )
        
    except Exception as e:
        print(f"❌ Error starting HTTPS server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()