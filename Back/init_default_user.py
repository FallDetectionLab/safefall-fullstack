#!/usr/bin/env python3
"""
Initialize default admin user for IoT device incident reporting

This script creates a default 'admin' user that Raspberry Pi devices
can use to report incidents. Run this after database initialization.

Usage:
    python init_default_user.py
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from models import db, User


def init_default_user():
    """Create default admin user if it doesn't exist"""
    app = create_app(os.getenv('FLASK_ENV', 'development'))

    with app.app_context():
        # Check if admin user already exists
        admin_user = User.query.filter_by(id='admin').first()

        if admin_user:
            print("✅ Default admin user already exists")
            print(f"   ID: {admin_user.id}")
            print(f"   Username: {admin_user.username}")
            print(f"   Email: {admin_user.email}")
            return True

        # Create default admin user
        try:
            admin_user = User(
                id='admin',  # String ID as defined in User model
                username='Administrator',
                email='admin@safefall.local'
            )
            admin_user.set_password('admin123')  # Default password

            db.session.add(admin_user)
            db.session.commit()

            print("=" * 60)
            print("✅ Default admin user created successfully!")
            print("=" * 60)
            print(f"   ID: {admin_user.id}")
            print(f"   Username: {admin_user.username}")
            print(f"   Email: {admin_user.email}")
            print(f"   Password: admin123 (CHANGE THIS IN PRODUCTION!)")
            print("=" * 60)
            print("\n⚠️  SECURITY WARNING:")
            print("   Change the default password immediately in production!")
            print("   This user is for IoT device incident reporting only.")
            print("=" * 60)

            return True

        except Exception as e:
            print(f"❌ Failed to create default user: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False


if __name__ == '__main__':
    print("🚀 SafeFall - Default User Initialization")
    print("=" * 60)

    success = init_default_user()

    if success:
        print("\n✅ Initialization complete!")
        print("   IoT devices can now report incidents using user_id='admin'")
    else:
        print("\n❌ Initialization failed!")
        sys.exit(1)
