#!/usr/bin/env python3
"""
Check MySQL Service Status
"""

import subprocess
import sys

def check_mysql_service():
    """Check MySQL service status on Windows."""
    print("🔍 Checking MySQL Service Status...")
    print("=" * 40)
    
    try:
        # Check MySQL80 service
        result = subprocess.run(['sc', 'query', 'MySQL80'], 
                              capture_output=True, text=True)
        
        print("MySQL80 Service Status:")
        print(result.stdout)
        
        if 'RUNNING' in result.stdout:
            print("✅ MySQL80 service is RUNNING")
            return True
        elif 'STOPPED' in result.stdout:
            print("❌ MySQL80 service is STOPPED")
            print("\n🔧 To start MySQL service:")
            print("1. Open Command Prompt as Administrator")
            print("2. Run: net start MySQL80")
            print("3. Or use Services.msc to start MySQL80 service")
            return False
        else:
            print("⚠️ MySQL80 service status unclear")
            return False
            
    except Exception as e:
        print(f"❌ Error checking service: {e}")
        return False

def check_mysql_processes():
    """Check if MySQL processes are running."""
    print("\n🔍 Checking MySQL Processes...")
    print("=" * 40)
    
    try:
        # Check for mysqld processes
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq mysqld.exe'], 
                              capture_output=True, text=True)
        
        if 'mysqld.exe' in result.stdout:
            print("✅ MySQL daemon (mysqld.exe) is running")
            print(result.stdout)
            return True
        else:
            print("❌ MySQL daemon (mysqld.exe) is not running")
            return False
            
    except Exception as e:
        print(f"❌ Error checking processes: {e}")
        return False

def check_mysql_port():
    """Check if MySQL port 3306 is listening."""
    print("\n🔍 Checking MySQL Port 3306...")
    print("=" * 40)
    
    try:
        # Check if port 3306 is listening
        result = subprocess.run(['netstat', '-an'], 
                              capture_output=True, text=True)
        
        lines = result.stdout.split('\n')
        mysql_ports = [line for line in lines if ':3306' in line and 'LISTENING' in line]
        
        if mysql_ports:
            print("✅ MySQL port 3306 is listening:")
            for port in mysql_ports:
                print(f"  {port.strip()}")
            return True
        else:
            print("❌ MySQL port 3306 is not listening")
            return False
            
    except Exception as e:
        print(f"❌ Error checking port: {e}")
        return False

def suggest_solutions():
    """Suggest solutions based on findings."""
    print("\n🔧 Troubleshooting Steps:")
    print("=" * 40)
    
    print("1. **Start MySQL Service:**")
    print("   - Open Command Prompt as Administrator")
    print("   - Run: net start MySQL80")
    print("   - Or use Services.msc to start MySQL80")
    
    print("\n2. **Check MySQL Workbench:**")
    print("   - Open MySQL Workbench")
    print("   - Try to connect to Local instance MySQL80")
    print("   - If it works, note the connection details")
    
    print("\n3. **Reset MySQL Password (if needed):**")
    print("   - Stop MySQL: net stop MySQL80")
    print("   - Start in safe mode: mysqld --skip-grant-tables")
    print("   - Connect: mysql -u root")
    print("   - Reset: ALTER USER 'root'@'localhost' IDENTIFIED BY 'newpassword';")
    print("   - Restart normally: net start MySQL80")
    
    print("\n4. **Alternative: Use MySQL Command Line:**")
    print("   - Try: mysql -u root -p")
    print("   - Enter your password when prompted")

def main():
    """Main function."""
    print("🚀 MySQL Service Diagnostic Tool")
    print("=" * 50)
    
    service_running = check_mysql_service()
    process_running = check_mysql_processes()
    port_listening = check_mysql_port()
    
    print("\n📊 Summary:")
    print("=" * 20)
    print(f"Service Status: {'✅ OK' if service_running else '❌ ISSUE'}")
    print(f"Process Running: {'✅ OK' if process_running else '❌ ISSUE'}")
    print(f"Port Listening: {'✅ OK' if port_listening else '❌ ISSUE'}")
    
    if service_running and process_running and port_listening:
        print("\n🎉 MySQL appears to be running correctly!")
        print("The issue might be with authentication.")
        print("Please verify your MySQL root password.")
    else:
        print("\n❌ MySQL is not running properly.")
        suggest_solutions()

if __name__ == "__main__":
    main()
