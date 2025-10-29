#!/usr/bin/env python3
"""
SafeFall - Default User Initialization Script
============================================================
Creates a default admin user for IoT device incident reporting
"""

from app import create_app
from models import db, User
from datetime import datetime, timezone

def init_default_user():
    """Initialize default admin user"""
    
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("🚀 SafeFall - Default User Initialization")
        print("="*60)
        
        # 기존 사용자 삭제 (있다면)
        old_admin = User.query.filter_by(id='admin').first()
        if old_admin:
            db.session.delete(old_admin)
            db.session.commit()
            print("🗑️  기존 'admin' 사용자 삭제됨")
        
        old_user_1 = User.query.filter_by(id='1').first()
        if old_user_1:
            db.session.delete(old_user_1)
            db.session.commit()
            print("🗑️  기존 ID='1' 사용자 삭제됨")
        
        # ID가 '1'인 기본 사용자 생성 (문자열!)
        default_user = User(
            id='1',  # 문자열 '1' (중요!)
            username='Administrator',
            email='admin@safefall.local'
        )
        
        # 비밀번호 설정
        default_user.set_password('admin123')
        
        db.session.add(default_user)
        db.session.commit()
        
        # 확인
        check_user = User.query.get('1')
        
        print("\n" + "="*60)
        print("✅ Default admin user created successfully!")
        print("="*60)
        print(f"   ID: '{check_user.id}' (문자열)")
        print(f"   Username: {check_user.username}")
        print(f"   Email: {check_user.email}")
        print(f"   Password: admin123 (CHANGE THIS IN PRODUCTION!)")
        print("="*60)
        
        print("\n⚠️  SECURITY WARNING:")
        print("   Change the default password immediately in production!")
        print("   This user is for IoT device incident reporting only.")
        print("="*60)
        
        print("\n✅ Initialization complete!")
        print(f"   IoT devices can now report incidents using user_id='1'")
        print()

if __name__ == '__main__':
    init_default_user()
