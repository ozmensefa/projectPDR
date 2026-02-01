# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import Counselor
from app.forms import LoginForm, RegistrationForm, ProfileForm, PasswordChangeForm
from app import db
import os
import uuid
from werkzeug.utils import secure_filename

auth_bp = Blueprint('auth', __name__)

def save_profile_photo(photo, counselor_id):
    """Profil fotoğrafını kaydet"""
    if photo and photo.filename:
        # Güvenli dosya adı oluştur
        filename = secure_filename(photo.filename)
        # Benzersiz dosya adı için UUID ekle
        name, ext = os.path.splitext(filename)
        unique_filename = f"counselor_{counselor_id}_{uuid.uuid4().hex[:8]}{ext}"
        
        # Upload klasörünü oluştur
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_photos')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Dosyayı kaydet
        photo_path = os.path.join(upload_folder, unique_filename)
        photo.save(photo_path)
        
        return unique_filename
    return None

def delete_profile_photo(filename):
    """Eski profil fotoğrafını sil"""
    if filename:
        photo_path = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_photos', filename)
        if os.path.exists(photo_path):
            os.remove(photo_path)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        counselor = Counselor.query.filter_by(email=form.email.data).first()
        if counselor and check_password_hash(counselor.password_hash, form.password.data):
            login_user(counselor)
            
            # Aktivite logu
            from app.utils.activity import log_activity
            log_activity('login', f'{counselor.name} sisteme giriş yaptı')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        flash('Geçersiz e-posta veya şifre')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    # Aktivite logu (logout'tan önce)
    from app.utils.activity import log_activity
    log_activity('logout', f'{current_user.name} sistemden çıkış yaptı')
    
    logout_user()
    flash('Başarıyla çıkış yaptınız.')
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # E-posta adresi kullanılıyor mu kontrol et
        if Counselor.query.filter_by(email=form.email.data).first():
            flash('Bu e-posta adresi zaten kullanılıyor.')
            return render_template('auth/register.html', form=form)
        
        counselor = Counselor(
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            name=form.name.data,
            title=form.title.data
        )
        db.session.add(counselor)
        db.session.commit()
        
        flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/profile')
@login_required
def profile():
    """Profil görüntüleme sayfası"""
    return render_template('auth/profile.html', counselor=current_user)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Profil düzenleme sayfası"""
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # E-posta değişikliği kontrolü (başka biri kullanıyor mu?)
        if form.email.data != current_user.email:
            existing_user = Counselor.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Bu e-posta adresi zaten başka bir kullanıcı tarafından kullanılıyor.', 'danger')
                return render_template('auth/edit_profile.html', form=form)
        
        # Eski fotoğraf bilgisini sakla
        old_photo = current_user.photo_filename
        
        # Form verilerini güncelle
        current_user.name = form.name.data
        current_user.email = form.email.data
        current_user.title = form.title.data
        
        # Eğer yeni fotoğraf yüklendiyse
        if form.photo.data:
            # Eski fotoğrafı sil
            if old_photo:
                delete_profile_photo(old_photo)
            # Yeni fotoğrafı kaydet
            photo_filename = save_profile_photo(form.photo.data, current_user.id)
            current_user.photo_filename = photo_filename
        
        db.session.commit()
        flash('Profil bilgileriniz başarıyla güncellendi.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html', form=form)

@auth_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Şifre değiştirme sayfası"""
    form = PasswordChangeForm()
    
    if form.validate_on_submit():
        # Mevcut şifre kontrolü
        if not check_password_hash(current_user.password_hash, form.current_password.data):
            flash('Mevcut şifreniz yanlış.', 'danger')
            return render_template('auth/change_password.html', form=form)
        
        # Yeni şifreyi kaydet
        current_user.password_hash = generate_password_hash(form.new_password.data)
        db.session.commit()
        
        flash('Şifreniz başarıyla değiştirildi.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html', form=form) 