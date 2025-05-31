#!/usr/bin/env python3
"""
Simple test to check if ZIP generation dependencies are working.
"""

def test_dependencies():
    """Test if all required dependencies are available."""
    print("🔍 Testing ZIP generation dependencies...")
    
    # Test zipfile (built-in)
    try:
        import zipfile
        print("✅ zipfile module available")
    except ImportError:
        print("❌ zipfile module not available")
        return False
    
    # Test tempfile (built-in)
    try:
        import tempfile
        print("✅ tempfile module available")
    except ImportError:
        print("❌ tempfile module not available")
        return False
    
    # Test pdfkit
    try:
        import pdfkit
        print("✅ pdfkit module available")
        
        # Test wkhtmltopdf
        try:
            # Try to create a simple PDF
            test_html = "<html><body><h1>Test</h1></body></html>"
            temp_dir = tempfile.gettempdir()
            test_pdf = os.path.join(temp_dir, "test.pdf")
            
            options = {
                'page-size': 'A4',
                'orientation': 'Portrait',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': 'UTF-8',
                'no-outline': None
            }
            
            pdfkit.from_string(test_html, test_pdf, options=options)
            
            if os.path.exists(test_pdf):
                print("✅ wkhtmltopdf working correctly")
                os.remove(test_pdf)  # Clean up
                return True
            else:
                print("❌ wkhtmltopdf failed to create PDF")
                return False
                
        except Exception as e:
            print(f"❌ wkhtmltopdf error: {str(e)}")
            print("💡 Solution: Download and install wkhtmltopdf from https://wkhtmltopdf.org/downloads.html")
            return False
            
    except ImportError:
        print("❌ pdfkit module not available")
        print("💡 Solution: pip install pdfkit")
        return False

def test_simple_zip_creation():
    """Test creating a simple ZIP file."""
    print("\n🔍 Testing simple ZIP creation...")
    
    try:
        import zipfile
        import tempfile
        import os
        
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        print(f"📁 Created temp directory: {temp_dir}")
        
        # Create a test text file
        test_file = os.path.join(temp_dir, "test_report.txt")
        with open(test_file, 'w') as f:
            f.write("This is a test individual report.\nStudent: Test Student\nGrade: Test Grade")
        
        # Create a ZIP file
        zip_path = os.path.join(temp_dir, "test_reports.zip")
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(test_file, "Individual_Report_Test_Student.txt")
        
        # Check if ZIP was created
        if os.path.exists(zip_path):
            zip_size = os.path.getsize(zip_path)
            print(f"✅ ZIP file created successfully: {zip_size} bytes")
            
            # Test reading the ZIP
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                files = zipf.namelist()
                print(f"✅ ZIP contains {len(files)} files: {files}")
            
            # Clean up
            os.remove(test_file)
            os.remove(zip_path)
            os.rmdir(temp_dir)
            
            return True
        else:
            print("❌ ZIP file was not created")
            return False
            
    except Exception as e:
        print(f"❌ ZIP creation failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("🚀 SIMPLE ZIP GENERATION TEST")
    print("=" * 50)
    
    # Import os here
    import os
    
    # Test dependencies
    deps_ok = test_dependencies()
    
    # Test ZIP creation
    zip_ok = test_simple_zip_creation()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"   Dependencies: {'✅ PASS' if deps_ok else '❌ FAIL'}")
    print(f"   ZIP Creation: {'✅ PASS' if zip_ok else '❌ FAIL'}")
    
    if deps_ok and zip_ok:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ ZIP generation should work in the Flask app.")
        print("\n📝 NEXT STEPS:")
        print("   1. Start your Flask app")
        print("   2. Go to Class Teacher Dashboard")
        print("   3. Try 'Download All Individual Reports (ZIP)'")
        print("   4. Check the browser console and Flask logs for any errors")
    else:
        print("\n❌ SOME TESTS FAILED!")
        if not deps_ok:
            print("   - Fix the dependency issues first")
        if not zip_ok:
            print("   - Check file permissions and disk space")
    
    return deps_ok and zip_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
