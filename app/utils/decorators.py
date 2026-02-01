# -*- coding: utf-8 -*-
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """Sadece admin kullanıcılar erişebilir"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Bu sayfaya erişmek için giriş yapmalısınız.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin:
            flash('Bu sayfaya erişim yetkiniz yok. Sadece adminler erişebilir.', 'danger')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

