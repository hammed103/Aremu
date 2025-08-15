#!/usr/bin/env python3
"""
Setup script for Aremu WhatsApp Bot
"""

import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            print("📝 Creating .env file from template...")
            with open(".env.example", "r") as example:
                content = example.read()
            with open(".env", "w") as env_file:
                env_file.write(content)
            print("✅ .env file created")
            print("⚠️  Please edit .env file with your actual API keys")
        else:
            print("⚠️  No .env.example found, please create .env manually")
    else:
        print("✅ .env file already exists")

def main():
    """Main setup function"""
    print("🤖 Aremu WhatsApp Bot Setup")
    print("=" * 40)
    
    check_python_version()
    install_dependencies()
    create_env_file()
    
    print()
    print("🎉 Setup complete!")
    print()
    print("Next steps:")
    print("1. Edit .env file with your API keys")
    print("2. Run: python app.py")
    print("3. Your bot will be available at http://localhost:5001")

if __name__ == "__main__":
    main()
