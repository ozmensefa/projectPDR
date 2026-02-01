# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, IntegerField, TextAreaField, SelectField, DateTimeLocalField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo, ValidationError
from datetime import datetime, timedelta

class LoginForm(FlaskForm):
    email = StringField('E-posta', validators=[DataRequired(), Email()])
    password = PasswordField('Şifre', validators=[DataRequired()])
    submit = SubmitField('Giriş Yap')

class ClientForm(FlaskForm):
    name = StringField('Ad Soyad', validators=[DataRequired(), Length(min=2, max=100)])
    age = IntegerField('Yaş', validators=[Optional()])
    gender = SelectField('Cinsiyet', 
                        choices=[('', 'Seçiniz'), ('E', 'Erkek'), ('K', 'Kadın'), ('D', 'Diğer')],
                        validators=[Optional()])
    contact = StringField('İletişim Bilgisi', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Notlar', validators=[Optional()])
    photo = FileField('Fotoğraf', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Sadece resim dosyaları kabul edilir!')])
    submit = SubmitField('Kaydet')

class SessionForm(FlaskForm):
    title = StringField('Oturum Başlığı', validators=[DataRequired()])
    session_date = DateTimeLocalField('Oturum Tarihi', validators=[DataRequired()], 
                                    default=datetime.now, format='%Y-%m-%dT%H:%M')
    notes = TextAreaField('Notlar', validators=[Optional()])
    submit = SubmitField('Kaydet')
    
    def validate_session_date(self, field):
        """Oturum tarihi doğrulaması"""
        if field.data:
            # Çok eski tarih kontrolü (1 yıl öncesinden eski olmasın)
            one_year_ago = datetime.now() - timedelta(days=365)
            if field.data < one_year_ago:
                raise ValidationError('Oturum tarihi 1 yıldan eski olamaz.')
            
            # Çok gelecek tarih kontrolü (1 yıl sonrasından ileri olmasın)
            one_year_later = datetime.now() + timedelta(days=365)
            if field.data > one_year_later:
                raise ValidationError('Oturum tarihi 1 yıldan fazla ileriye ayarlanamaz.')

class RegistrationForm(FlaskForm):
    email = StringField('E-posta', validators=[DataRequired(), Email()])
    password = PasswordField('Şifre', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Şifre (Tekrar)', 
        validators=[DataRequired(), EqualTo('password', message='Şifreler eşleşmiyor')])
    name = StringField('Ad Soyad', validators=[DataRequired(), Length(min=2, max=100)])
    title = StringField('Unvan', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Kayıt Ol')

class ProfileForm(FlaskForm):
    name = StringField('Ad Soyad', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('E-posta', validators=[DataRequired(), Email()])
    title = StringField('Unvan', validators=[Optional(), Length(max=100)])
    photo = FileField('Profil Fotoğrafı', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Sadece resim dosyaları kabul edilir!')])
    submit = SubmitField('Profili Güncelle')

class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Mevcut Şifre', validators=[DataRequired()])
    new_password = PasswordField('Yeni Şifre', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Yeni Şifre (Tekrar)', 
        validators=[DataRequired(), EqualTo('new_password', message='Şifreler eşleşmiyor')])
    submit = SubmitField('Şifreyi Değiştir') 