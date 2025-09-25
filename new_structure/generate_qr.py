"""
QR Code Generator for Easy Mobile Access
Generates a QR code that users can scan to access the site
"""

import qrcode
from PIL import Image, ImageDraw, ImageFont
import os

def generate_mobile_qr():
    """Generate QR code for mobile access"""
    url = "http://192.168.1.124:8080"
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Create a larger image with text
    img_width = 400
    img_height = 500
    img = Image.new('RGB', (img_width, img_height), 'white')
    
    # Paste QR code
    qr_img = qr_img.resize((300, 300))
    img.paste(qr_img, (50, 100))
    
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to use a nice font
        font_title = ImageFont.truetype("arial.ttf", 24)
        font_text = ImageFont.truetype("arial.ttf", 16)
        font_url = ImageFont.truetype("arial.ttf", 12)
    except:
        # Fallback to default font
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_url = ImageFont.load_default()
    
    # Add title
    draw.text((50, 20), "🎓 Hillview School", font=font_title, fill="black")
    draw.text((50, 50), "Scan to access on mobile", font=font_text, fill="gray")
    
    # Add URL
    draw.text((50, 420), url, font=font_url, fill="blue")
    draw.text((50, 440), "Connect to same WiFi network first!", font=font_url, fill="red")
    
    # Save QR code
    qr_path = "mobile_access_qr.png"
    img.save(qr_path)
    
    return qr_path, url

if __name__ == "__main__":
    try:
        qr_path, url = generate_mobile_qr()
        print("📱 QR CODE GENERATED FOR MOBILE ACCESS")
        print("=" * 45)
        print(f"✅ QR Code saved as: {qr_path}")
        print(f"🌐 URL: {url}")
        print("\n📋 Instructions:")
        print("1. Make sure your phone is on the same WiFi network")
        print("2. Open camera app or QR scanner on your phone")
        print(f"3. Scan the QR code in {qr_path}")
        print("4. Tap the link to open in browser")
        print("\n💡 Alternative: Manually type the URL in your phone browser")
        print("=" * 45)
        
        # Try to open the QR code image
        try:
            os.startfile(qr_path)  # Windows
        except:
            try:
                os.system(f"open {qr_path}")  # macOS
            except:
                print(f"📁 Please open {qr_path} to view the QR code")
                
    except ImportError:
        print("❌ QR code libraries not installed")
        print("📱 Manual access: http://192.168.1.124:8080")
        print("1. Connect phone to same WiFi")
        print("2. Open browser on phone")
        print("3. Type: http://192.168.1.124:8080")
    except Exception as e:
        print(f"❌ Error generating QR code: {e}")
        print("📱 Manual access: http://192.168.1.124:8080")