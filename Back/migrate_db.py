"""
Database migration script
Incident 테이블에 video_blob, thumbnail_blob 컬럼 추가
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from models import db

def migrate_database():
    """데이터베이스 마이그레이션"""
    app = create_app()
    
    with app.app_context():
        print("🔧 데이터베이스 마이그레이션 시작...")
        
        try:
            # video_blob, thumbnail_blob 컬럼 추가
            db.session.execute(db.text("""
                ALTER TABLE incidents 
                ADD COLUMN video_blob BLOB
            """))
            print("✅ video_blob 컬럼 추가 완료")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("ℹ️  video_blob 컬럼 이미 존재")
            else:
                print(f"⚠️  video_blob 컬럼 추가 실패: {e}")
        
        try:
            db.session.execute(db.text("""
                ALTER TABLE incidents 
                ADD COLUMN thumbnail_blob BLOB
            """))
            print("✅ thumbnail_blob 컬럼 추가 완료")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("ℹ️  thumbnail_blob 컬럼 이미 존재")
            else:
                print(f"⚠️  thumbnail_blob 컬럼 추가 실패: {e}")
        
        try:
            db.session.commit()
            print("✅ 마이그레이션 완료!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ 마이그레이션 실패: {e}")

if __name__ == '__main__':
    migrate_database()
