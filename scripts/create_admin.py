# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Counselor
from werkzeug.security import generate_password_hash

def create_admin_user(email, password, name, title=None):
    app = create_app()
    with app.app_context():
        # Kullanıcı zaten var mı kontrol et
        existing_user = Counselor.query.filter_by(email=email).first()
        if existing_user:
            print(f"'{email}' adresi ile kayıtlı bir kullanıcı zaten var!")
            return

        # Yeni admin kullanıcı oluştur
        admin = Counselor(
            email=email,
            password_hash=generate_password_hash(password),
            name=name,
            title=title
        )

        try:
            db.session.add(admin)
            db.session.commit()
            print(f"Admin kullanıcı başarıyla oluşturuldu: {email}")
        except Exception as e:
            print(f"Hata oluştu: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Kullanım: python create_admin.py <email> <password> <name> [title]")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]
    name = sys.argv[3]
    title = sys.argv[4] if len(sys.argv) > 4 else None

    create_admin_user(email, password, name, title) 