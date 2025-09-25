#!/usr/bin/env python3
"""
Production run script for the Hillview School Management System.
This script configures the application for production deployment with HTTPS support.
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
        os.path.join(current_dir, '.env.production'),
        os.path.join(current_dir, '.env'),
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

def create_ssl_context():
    """Create SSL context for HTTPS."""
    # Check for SSL certificate files
    cert_file = os.environ.get('SSL_CERT_FILE', 'ssl/cert.pem')
    key_file = os.environ.get('SSL_KEY_FILE', 'ssl/key.pem')
    
    cert_path = os.path.join(current_dir, cert_file)
    key_path = os.path.join(current_dir, key_file)
    
    if os.path.exists(cert_path) and os.path.exists(key_path):
        print(f"🔐 Using SSL certificates: {cert_file}, {key_file}")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_path, key_path)
        return context
    else:
        print("⚠️ SSL certificates not found. Generating self-signed certificate...")
        return generate_self_signed_cert()

def generate_self_signed_cert():
    """Generate self-signed SSL certificate for development/testing."""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime
        
        # Create SSL directory if it doesn't exist
        ssl_dir = os.path.join(current_dir, 'ssl')
        os.makedirs(ssl_dir, exist_ok=True)
        
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
        cert_path = os.path.join(ssl_dir, 'cert.pem')
        key_path = os.path.join(ssl_dir, 'key.pem')
        
        with open(cert_path, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
            
        with open(key_path, 'wb') as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print(f"✅ Self-signed certificate generated: {cert_path}")
        print(f"✅ Private key generated: {key_path}")
        
        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_path, key_path)
        return context
        
    except ImportError:
        print("❌ cryptography library not installed. Install with: pip install cryptography")
        print("📝 For production, use proper SSL certificates from a Certificate Authority")
        return 'adhoc'  # Flask will generate adhoc SSL context
    except Exception as e:
        print(f"❌ Error generating SSL certificate: {e}")
        return 'adhoc'

def main():
    """Main function to run the production application."""
    _load_env_file()
    
    try:
        # Configuration
        PORT = int(os.environ.get('PORT', 8443))  # Default HTTPS port
        HOST = os.environ.get('HOST', '0.0.0.0')
        USE_SSL = os.environ.get('USE_SSL', 'true').lower() in ('true', '1', 'yes')
        
        # Production environment setup
        os.environ['FLASK_ENV'] = 'production'
        
        print("🚀 Hillview School Management System - Production Mode")
        
        if USE_SSL:
            print(f"🔐 HTTPS Server starting on: https://{HOST}:{PORT}")
            ssl_context = create_ssl_context()
        else:
            print(f"🌐 HTTP Server starting on: http://{HOST}:{PORT}")
            print("⚠️ WARNING: Running without SSL in production is not recommended!")
            ssl_context = None
        
        print("⏳ Initializing production application...")
        
        # Import create_app from the new_structure package
        from new_structure import create_app
        
        # Create the Flask application in production mode
        app = create_app('production')
        
        print("✅ Production application initialized successfully")
        print("🛡️ Security features enabled:")
        print("  • HTTPS/SSL encryption")
        print("  • Secure cookie settings")
        print("  • CSRF protection")
        print("  • Rate limiting")
        print("  • Security headers")
        print("  • Input sanitization")
        print("🌐 Ready to accept connections...")
        print("")
        
        if USE_SSL:
            print("📝 Note: If using self-signed certificate, browsers will show security warning")
            print("   For production, use certificates from a trusted Certificate Authority")
        
        # Run the application
        app.run(
            host=HOST,
            port=PORT,
            debug=False,
            ssl_context=ssl_context if USE_SSL else None,
            threaded=True,
            use_reloader=False
        )
        
    except Exception as e:
        print(f"❌ Error starting production application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    # Add ipaddress import for certificate generation
    import ipaddress
    main()