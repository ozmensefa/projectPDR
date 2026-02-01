# -*- coding: utf-8 -*-
from app import db
from app.models import UserActivity
from flask_login import current_user

def log_activity(action, description=None):
    """Kullanıcı aktivitesini kaydet"""
    if not current_user.is_authenticated:
        return
    
    try:
        activity = UserActivity(
            counselor_id=current_user.id,
            action=action,
            description=description
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        print(f"Activity log hatası: {e}")
        db.session.rollback()

