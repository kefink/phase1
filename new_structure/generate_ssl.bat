@echo off
echo 🔐 Generating SSL Certificate for HTTPS Deployment...

REM Create ssl directory if it doesn't exist
if not exist "ssl" (
    mkdir ssl
    echo ✅ Created ssl directory
)

REM Generate self-signed certificate
echo 🔑 Generating SSL certificate and private key...

openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=HillviewSchool/OU=IT/CN=localhost"

if %errorlevel% == 0 (
    echo ✅ SSL certificate generated successfully!
    echo    📁 Certificate: ssl/cert.pem
    echo    🔑 Private Key: ssl/key.pem
    echo    ⏰ Valid for: 365 days
    echo.
    echo 🚀 Next steps:
    echo 1. Start your Flask app: python run.py
    echo 2. Start Nginx: nginx -c nginx.conf
    echo 3. Access: https://localhost
    echo.
    echo ⚠️  Note: Browsers will show a security warning for self-signed certificates.
    echo    Click 'Advanced' and 'Proceed to localhost' to continue.
) else (
    echo ❌ Failed to generate SSL certificate
    echo Make sure OpenSSL is installed on your system
    echo You can install it from: https://slproweb.com/products/Win32OpenSSL.html
)

pause