# -*- coding: utf-8 -*-
"""
Resend ile e-posta gönderim servisi
"""
import resend
from flask import current_app


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
