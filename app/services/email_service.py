# -*- coding: utf-8 -*-
"""
Resend ile e-posta gönderim servisi
"""
import resend
from flask import current_app


def _send_email(to_email, subject, html_content):
    """Ortak e-posta gönderim fonksiyonu"""
    resend.api_key = current_app.config['RESEND_API_KEY']
    try:
        params = {
            "from": current_app.config['RESEND_FROM_EMAIL'],
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        email = resend.Emails.send(params)
        current_app.logger.info(f"E-posta gönderildi: {to_email} - {subject} (ID: {email.get('id', 'N/A')})")
        return True
    except Exception as e:
        current_app.logger.error(f"E-posta gönderimi başarısız: {to_email} - Hata: {str(e)}")
        return False


def _build_email(name, heading, body_html, button_text=None, button_url=None):
    """Ortak e-posta HTML şablonu oluşturur"""
    button_block = ""
    if button_text and button_url:
        button_block = f"""
        <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 0 auto;">
            <tr>
                <td style="border-radius: 8px; background: linear-gradient(135deg, #4a90d9 0%, #357abd 100%);">
                    <a href="{button_url}" target="_blank"
                       style="display: inline-block; padding: 14px 36px; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600; letter-spacing: 0.5px;">
                        {button_text}
                    </a>
                </td>
            </tr>
        </table>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f4f7fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f4f7fa; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); overflow: hidden;">
                        <tr>
                            <td style="background: linear-gradient(135deg, #4a90d9 0%, #357abd 100%); padding: 32px 40px; text-align: center;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">
                                    YAKADES
                                </h1>
                                <p style="color: rgba(255,255,255,0.85); margin: 6px 0 0 0; font-size: 14px;">
                                    PDR Video Analiz Sistemi
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="color: #2d3748; margin: 0 0 8px 0; font-size: 20px;">
                                    {heading}
                                </h2>
                                <p style="color: #718096; margin: 0 0 24px 0; font-size: 14px;">
                                    Merhaba {name},
                                </p>
                                {body_html}
                                {button_block}
                            </td>
                        </tr>
                        <tr>
                            <td style="background-color: #f7fafc; padding: 24px 40px; text-align: center; border-top: 1px solid #e2e8f0;">
                                <p style="color: #a0aec0; font-size: 12px; margin: 0;">
                                    &copy; 2026 YAKADES - PDR Video Analiz Sistemi | yakades.com.tr
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def send_analysis_completed_email(to_email, name, client_name, session_title, view_url):
    """Oturum analizi tamamlandığında danışmana e-posta gönderir."""
    body = f"""
    <div style="background: #f0fff4; border-left: 4px solid #48bb78; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
        <p style="color: #276749; font-size: 16px; font-weight: 600; margin: 0 0 4px 0;">
            &#10004; Oturum Analizi Tamamlandı
        </p>
        <p style="color: #2f855a; font-size: 14px; margin: 0;">
            Analiz sonuçları incelemenize hazır.
        </p>
    </div>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
        <tr>
            <td style="padding: 10px 0; color: #718096; font-size: 14px; border-bottom: 1px solid #e2e8f0; width: 120px;">Danışan</td>
            <td style="padding: 10px 0; color: #2d3748; font-size: 14px; font-weight: 600; border-bottom: 1px solid #e2e8f0;">{client_name}</td>
        </tr>
        <tr>
            <td style="padding: 10px 0; color: #718096; font-size: 14px; border-bottom: 1px solid #e2e8f0;">Oturum</td>
            <td style="padding: 10px 0; color: #2d3748; font-size: 14px; font-weight: 600; border-bottom: 1px solid #e2e8f0;">{session_title}</td>
        </tr>
    </table>
    """
    html = _build_email(name, "Oturum Analizi Tamamlandı", body, "Sonuçları Görüntüle", view_url)
    return _send_email(to_email, f"Analiz Tamamlandı - {client_name} / {session_title}", html)


def send_analysis_failed_email(to_email, name, client_name, session_title, view_url):
    """Oturum analizi başarısız olduğunda danışmana e-posta gönderir."""
    body = f"""
    <div style="background: #fff5f5; border-left: 4px solid #fc8181; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
        <p style="color: #9b2c2c; font-size: 16px; font-weight: 600; margin: 0 0 4px 0;">
            &#10060; Oturum Analizi Başarısız
        </p>
        <p style="color: #c53030; font-size: 14px; margin: 0;">
            Analiz sırasında bir hata oluştu. Lütfen tekrar deneyin.
        </p>
    </div>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
        <tr>
            <td style="padding: 10px 0; color: #718096; font-size: 14px; border-bottom: 1px solid #e2e8f0; width: 120px;">Danışan</td>
            <td style="padding: 10px 0; color: #2d3748; font-size: 14px; font-weight: 600; border-bottom: 1px solid #e2e8f0;">{client_name}</td>
        </tr>
        <tr>
            <td style="padding: 10px 0; color: #718096; font-size: 14px; border-bottom: 1px solid #e2e8f0;">Oturum</td>
            <td style="padding: 10px 0; color: #2d3748; font-size: 14px; font-weight: 600; border-bottom: 1px solid #e2e8f0;">{session_title}</td>
        </tr>
    </table>
    """
    html = _build_email(name, "Oturum Analizi Başarısız", body, "Oturuma Git", view_url)
    return _send_email(to_email, f"Analiz Başarısız - {client_name} / {session_title}", html)


def send_progress_completed_email(to_email, name, client_name, date_range, view_url):
    """İlerleyiş analizi tamamlandığında danışmana e-posta gönderir."""
    body = f"""
    <div style="background: #ebf8ff; border-left: 4px solid #4299e1; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
        <p style="color: #2a4365; font-size: 16px; font-weight: 600; margin: 0 0 4px 0;">
            &#128202; İlerleyiş Analizi Hazır
        </p>
        <p style="color: #2b6cb0; font-size: 14px; margin: 0;">
            Danışanınızın ilerleyiş raporu incelemenize hazır.
        </p>
    </div>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
        <tr>
            <td style="padding: 10px 0; color: #718096; font-size: 14px; border-bottom: 1px solid #e2e8f0; width: 120px;">Danışan</td>
            <td style="padding: 10px 0; color: #2d3748; font-size: 14px; font-weight: 600; border-bottom: 1px solid #e2e8f0;">{client_name}</td>
        </tr>
        <tr>
            <td style="padding: 10px 0; color: #718096; font-size: 14px; border-bottom: 1px solid #e2e8f0;">Tarih Aralığı</td>
            <td style="padding: 10px 0; color: #2d3748; font-size: 14px; font-weight: 600; border-bottom: 1px solid #e2e8f0;">{date_range}</td>
        </tr>
    </table>
    """
    html = _build_email(name, "İlerleyiş Analizi Tamamlandı", body, "Raporu Görüntüle", view_url)
    return _send_email(to_email, f"İlerleyiş Analizi Hazır - {client_name}", html)


def send_progress_failed_email(to_email, name, client_name, error_msg):
    """İlerleyiş analizi başarısız olduğunda danışmana e-posta gönderir."""
    body = f"""
    <div style="background: #fff5f5; border-left: 4px solid #fc8181; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
        <p style="color: #9b2c2c; font-size: 16px; font-weight: 600; margin: 0 0 4px 0;">
            &#10060; İlerleyiş Analizi Başarısız
        </p>
        <p style="color: #c53030; font-size: 14px; margin: 0;">
            Analiz sırasında bir hata oluştu: {error_msg}
        </p>
    </div>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
        <tr>
            <td style="padding: 10px 0; color: #718096; font-size: 14px; border-bottom: 1px solid #e2e8f0; width: 120px;">Danışan</td>
            <td style="padding: 10px 0; color: #2d3748; font-size: 14px; font-weight: 600; border-bottom: 1px solid #e2e8f0;">{client_name}</td>
        </tr>
    </table>
    """
    html = _build_email(name, "İlerleyiş Analizi Başarısız", body)
    return _send_email(to_email, f"İlerleyiş Analizi Başarısız - {client_name}", html)


def send_verification_email(to_email, name, verification_url):
    """
    Kayıt sonrası e-posta doğrulama linki gönderir.
    
    Args:
        to_email: Alıcı e-posta adresi
        name: Kullanıcının adı
        verification_url: Doğrulama linki (tam URL)
    
    Returns:
        bool: Başarılı ise True, hata ise False
    """
    resend.api_key = current_app.config['RESEND_API_KEY']
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f4f7fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f4f7fa; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); overflow: hidden;">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #4a90d9 0%, #357abd 100%); padding: 32px 40px; text-align: center;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">
                                    PDR Video Analiz Sistemi
                                </h1>
                            </td>
                        </tr>
                        <!-- Body -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="color: #2d3748; margin: 0 0 16px 0; font-size: 20px;">
                                    Merhaba {name},
                                </h2>
                                <p style="color: #4a5568; font-size: 16px; line-height: 1.6; margin: 0 0 24px 0;">
                                    PDR Video Analiz Sistemi'ne kayıt olduğunuz için teşekkür ederiz. 
                                    Hesabınızı aktifleştirmek için lütfen aşağıdaki butona tıklayın.
                                </p>
                                <!-- Button -->
                                <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 0 auto;">
                                    <tr>
                                        <td style="border-radius: 8px; background: linear-gradient(135deg, #4a90d9 0%, #357abd 100%);">
                                            <a href="{verification_url}" 
                                               target="_blank"
                                               style="display: inline-block; padding: 14px 36px; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600; letter-spacing: 0.5px;">
                                                E-posta Adresimi Doğrula
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                <p style="color: #718096; font-size: 14px; line-height: 1.6; margin: 24px 0 0 0;">
                                    Buton çalışmıyorsa, aşağıdaki linki tarayıcınıza yapıştırabilirsiniz:
                                </p>
                                <p style="color: #4a90d9; font-size: 13px; word-break: break-all; margin: 8px 0 0 0;">
                                    {verification_url}
                                </p>
                                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 32px 0;">
                                <p style="color: #a0aec0; font-size: 13px; line-height: 1.5; margin: 0;">
                                    Bu link 24 saat geçerlidir. Eğer bu kayıt işlemini siz yapmadıysanız, 
                                    bu e-postayı görmezden gelebilirsiniz.
                                </p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f7fafc; padding: 24px 40px; text-align: center; border-top: 1px solid #e2e8f0;">
                                <p style="color: #a0aec0; font-size: 12px; margin: 0;">
                                    &copy; 2026 PDR Video Analiz Sistemi | yakades.com.tr
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    try:
        params = {
            "from": current_app.config['RESEND_FROM_EMAIL'],
            "to": [to_email],
            "subject": "E-posta Adresinizi Doğrulayın - PDR Video Analiz",
            "html": html_content,
        }
        
        email = resend.Emails.send(params)
        current_app.logger.info(f"Doğrulama e-postası gönderildi: {to_email} (ID: {email.get('id', 'N/A')})")
        return True
    except Exception as e:
        current_app.logger.error(f"E-posta gönderimi başarısız: {to_email} - Hata: {str(e)}")
        return False
