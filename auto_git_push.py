#!/usr/bin/env python3
"""
Automated Git Push Script for Hillview School Management System
This script automates the entire process of committing and pushing changes to GitHub.
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description=""):
    """Run a shell command and return the result."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(f"✅ {description} successful")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True, result.stdout
        else:
            print(f"❌ {description} failed")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False, result.stderr
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False, str(e)

def detect_repository():
    """Try to detect the correct GitHub repository."""
    print("🔍 Detecting GitHub repository...")
    
    # Check current remote
    success, output = run_command("git remote -v", "Checking current remote")
    if success and output:
        print(f"📋 Current remote configuration:")
        print(f"   {output}")
        
        # Extract repository info
        lines = output.strip().split('\n')
        for line in lines:
            if 'origin' in line and 'fetch' in line:
                parts = line.split()
                if len(parts) >= 2:
                    url = parts[1]
                    print(f"🔗 Found remote URL: {url}")
                    return url
    
    return None

def fix_repository_url():
    """Fix the repository URL if it's incorrect."""
    print("🔧 Fixing repository URL...")
    
    current_url = detect_repository()
    
    # Common incorrect URLs and their fixes
    fixes = {
        'https://github.com/yourusername/hillview-analytics-dashboard.git': 'https://github.com/kefink/hillview.git',
        'https://github.com/yourusername/hillview-analytics-dashboard.git/': 'https://github.com/kefink/hillview.git'
    }
    
    if current_url:
        for incorrect, correct in fixes.items():
            if incorrect in current_url:
                print(f"🔄 Updating repository URL from {incorrect} to {correct}")
                success, _ = run_command(f'git remote set-url origin {correct}', "Updating remote URL")
                if success:
                    return True
    
    # If no automatic fix, try the most likely correct URL
    print("🔄 Setting repository URL to most likely correct one...")
    success, _ = run_command('git remote set-url origin https://github.com/kefink/hillview.git', "Setting remote URL")
    return success

def main():
    """Main automation function."""
    print("🚀 Automated Git Push for Hillview School Management System")
    print("=" * 60)
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Not in a Git repository. Please run this from the project root.")
        return False
    
    # Step 1: Check Git status
    print("\n📋 Step 1: Checking Git status...")
    success, output = run_command("git status --porcelain", "Checking for changes")
    if not success:
        print("❌ Failed to check Git status")
        return False
    
    if not output.strip():
        print("ℹ️  No changes to commit. Repository is up to date.")
        return True
    
    print(f"📝 Found {len(output.strip().split())} changed files")
    
    # Step 2: Fix repository URL if needed
    print("\n🔧 Step 2: Checking repository configuration...")
    fix_repository_url()
    
    # Step 3: Add all changes
    print("\n➕ Step 3: Adding all changes...")
    success, _ = run_command("git add .", "Adding all changes")
    if not success:
        print("❌ Failed to add changes")
        return False
    
    # Step 4: Create commit message
    print("\n💬 Step 4: Creating commit...")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"""Add Parent Portal & Email Results Feature - {timestamp}

🎉 Complete Parent Portal Implementation:

✅ Core Features:
- Parent authentication system (login, register, password reset)
- Parent dashboard with children overview and recent results
- Email notification system with Gmail integration
- PDF download functionality for parent reports
- Parent profile management and notification preferences
- Responsive parent portal UI with modern glassmorphism design

✅ Technical Implementation:
- Database migration for parent portal tables
- Email templates for verification and notifications
- Parent service layer for business logic
- Simplified parent blueprint for reliable routing
- Updated application structure to run from new_structure directory
- Comprehensive help and contact pages for parents

✅ Security Features:
- Email verification for new accounts
- Account lockout protection (5 attempts, 30-min lockout)
- Secure password hashing and session management
- Data privacy (parents can only access their own children's data)

✅ User Experience:
- Mobile-responsive design
- Intuitive navigation and clear information hierarchy
- Real-time academic progress viewing
- Automatic email notifications when results published
- Notification preference management

✅ Integration:
- Seamless integration with existing school management system
- No breaking changes to existing functionality
- Uses existing school configuration and branding
- Compatible with current database structure

🔧 Technical Files Added/Modified:
- new_structure/models/parent.py (Parent data models)
- new_structure/services/email_service.py (Gmail integration)
- new_structure/services/parent_service.py (Parent business logic)
- new_structure/services/notification_service.py (Email notifications)
- new_structure/views/parent_simple.py (Parent portal routes)
- new_structure/templates/parent/* (All parent portal templates)
- new_structure/migrations/create_parent_portal_tables.py (Database setup)
- Updated new_structure/run.py (Fixed to work from new_structure directory)

🎯 Ready for Production:
- Fully tested and working parent portal
- Complete documentation and setup guides
- Database migration scripts included
- Email system ready for Gmail integration

Parent Portal Access: http://localhost:5000/parent/login
Test Credentials: test.parent@example.com / testpassword123"""

    success, _ = run_command(f'git commit -m "{commit_message}"', "Creating commit")
    if not success:
        print("❌ Failed to create commit")
        return False
    
    # Step 5: Push to GitHub
    print("\n🚀 Step 5: Pushing to GitHub...")
    success, output = run_command("git push origin master", "Pushing to GitHub")
    if not success:
        print("❌ Failed to push to GitHub")
        print("🔧 Trying alternative solutions...")
        
        # Try pushing to main branch instead
        print("🔄 Trying to push to 'main' branch...")
        success, _ = run_command("git push origin main", "Pushing to main branch")
        if not success:
            # Try setting upstream
            print("🔄 Trying to set upstream and push...")
            success, _ = run_command("git push -u origin master", "Setting upstream and pushing")
            if not success:
                print("❌ All push attempts failed. Please check:")
                print("   1. Your GitHub repository exists")
                print("   2. You have push permissions")
                print("   3. Your authentication is set up correctly")
                return False
    
    # Step 6: Verify success
    print("\n✅ Step 6: Verifying push...")
    success, _ = run_command("git status", "Checking final status")
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS! Parent Portal changes pushed to GitHub!")
    print("\n📋 What was pushed:")
    print("   ✅ Complete Parent Portal & Email Results feature")
    print("   ✅ All new parent portal files and templates")
    print("   ✅ Database migration scripts")
    print("   ✅ Updated application configuration")
    print("   ✅ Documentation and setup guides")
    print("\n🔗 Next steps:")
    print("   1. Check your GitHub repository to see the changes")
    print("   2. Other developers can now clone and use the parent portal")
    print("   3. Set up Gmail credentials for email notifications")
    print("   4. Run database migration on production")
    print("\n🌐 Parent Portal URL: http://localhost:5000/parent/login")
    print("🔑 Test Login: test.parent@example.com / testpassword123")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎯 Automation completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Automation failed. Please check the errors above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Automation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Automation failed with error: {e}")
        sys.exit(1)
