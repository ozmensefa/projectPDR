# -*- coding: utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.models import *
from app import create_app, db

app = create_app()
migrate = Migrate(app, db)

def init_db():
    app = create_app()
    with app.app_context():
        print("Veritabanı sıfırlanıyor...")
        db.drop_all()
        db.create_all()
        print("Veritabanı sıfırlandı!")

if __name__ == '__main__':
    init_db() 