#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Admin kullanıcı oluşturma scripti
Kullanım: python3 make_admin.py email@example.com
"""
import sys
from app import create_app, db
from app.models import Counselor

def make_admin(email):
    """Belirtilen email adresine sahip kullanıcıyı admin yapar"""
    app = create_app()
    with app.app_context():
        user = Counselor.query.filter_by(email=email).first()
        
        if not user:
            print(f"❌ '{email}' email adresine sahip kullanıcı bulunamadı!")
            print("\n📋 Mevcut kullanıcılar:")
            users = Counselor.query.all()
            for u in users:
                admin_status = "⭐ Admin" if u.is_admin else "Kullanıcı"
                print(f"   - {u.name} ({u.email}) - {admin_status}")
            return False
        
        if user.is_admin:
            print(f"ℹ️  {user.name} ({email}) zaten admin!")
            return True
        
        user.is_admin = True
        db.session.commit()
        print(f"✅ {user.name} ({email}) admin yapıldı!")
        return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Kullanım: python3 make_admin.py email@example.com")
        print("\n📋 Mevcut kullanıcılar:")
        app = create_app()
        with app.app_context():
            users = Counselor.query.all()
            for u in users:
                admin_status = "⭐ Admin" if u.is_admin else "Kullanıcı"
                print(f"   - {u.name} ({u.email}) - {admin_status}")
        sys.exit(1)
    
    email = sys.argv[1]
    success = make_admin(email)
    sys.exit(0 if success else 1)

