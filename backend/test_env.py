#!/usr/bin/env python3
"""
Test script to verify that all environment variables are properly loaded.
This script tests the environment variable configuration for the vehicle detection system.
"""

import os
from dotenv import load_dotenv

def test_environment_variables():
    """Test if all required environment variables are properly loaded."""
    
    # Load environment variables from .env file
    load_dotenv()
    
    print("🔧 Testing Environment Variable Configuration")
    print("=" * 50)
    
    # Test database configuration
    print("\n📊 Database Configuration:")
    mysql_password = os.getenv('MYSQL_PASSWORD')
    if mysql_password:
        print(f"✅ MYSQL_PASSWORD: Found (length: {len(mysql_password)} chars)")
    else:
        print("❌ MYSQL_PASSWORD: Not found!")
    
    # Test email configuration
    print("\n📧 Email Configuration:")
    email_sender = os.getenv('EMAIL_SENDER')
    if email_sender:
        print(f"✅ EMAIL_SENDER: {email_sender}")
    else:
        print("❌ EMAIL_SENDER: Not found!")
    
    email_password = os.getenv('EMAIL_PASSWORD')
    if email_password:
        print(f"✅ EMAIL_PASSWORD: Found (length: {len(email_password)} chars)")
    else:
        print("❌ EMAIL_PASSWORD: Not found!")
    
    email_receiver = os.getenv('EMAIL_RECEIVER')
    if email_receiver:
        print(f"✅ EMAIL_RECEIVER: {email_receiver}")
    else:
        print("❌ EMAIL_RECEIVER: Not found!")
    
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = os.getenv('SMTP_PORT', '587')
    email_enabled = os.getenv('EMAIL_ENABLED', 'true')
    
    print(f"✅ SMTP_SERVER: {smtp_server}")
    print(f"✅ SMTP_PORT: {smtp_port}")
    print(f"✅ EMAIL_ENABLED: {email_enabled}")
    
    # Test import from config modules
    print("\n🔧 Configuration Module Tests:")
    try:
        from config import DB_CONFIG
        print("✅ Database config imported successfully")
        print(f"   - Host: {DB_CONFIG.get('host', 'Not set')}")
        print(f"   - User: {DB_CONFIG.get('user', 'Not set')}")
        print(f"   - Database: {DB_CONFIG.get('database', 'Not set')}")
        print(f"   - Password: {'Set' if DB_CONFIG.get('password') else 'Not set'}")
    except Exception as e:
        print(f"❌ Error importing database config: {e}")
    
    try:
        from email_config import EMAIL_SENDER as cfg_sender, EMAIL_PASSWORD as cfg_password
        print("✅ Email config imported successfully")
        print(f"   - Sender: {cfg_sender}")
        print(f"   - Password: {'Set' if cfg_password else 'Not set'}")
    except Exception as e:
        print(f"❌ Error importing email config: {e}")
    
    print("\n🎉 Environment variable test completed!")

if __name__ == "__main__":
    test_environment_variables()
