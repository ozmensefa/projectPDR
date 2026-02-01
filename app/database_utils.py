# -*- coding: utf-8 -*-
import time
import functools
from sqlalchemy.exc import OperationalError, DisconnectionError
from app import db

def retry_db_operation(max_retries=3, delay=1):
    """Veritabanı işlemleri için retry decorator"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DisconnectionError) as e:
                    last_exception = e
                    error_msg = str(e).lower()
                    
                    # Disk I/O hatası veya veritabanı kilidi
                    if 'disk i/o error' in error_msg or 'database is locked' in error_msg:
                        print(f"⚠️ Veritabanı hatası (Deneme {attempt + 1}/{max_retries}): {e}")
                        
                        if attempt < max_retries - 1:
                            # Bağlantıyı temizle
                            try:
                                db.session.rollback()
                                db.session.close()
                            except:
                                pass
                            
                            # Exponential backoff
                            wait_time = delay * (2 ** attempt)
                            print(f"🔄 {wait_time} saniye bekleniyor...")
                            time.sleep(wait_time)
                        else:
                            print(f"❌ Maksimum deneme sayısına ulaşıldı: {e}")
                            raise last_exception
                    else:
                        # Diğer hatalar için hemen fırlat
                        raise e
                except Exception as e:
                    # Diğer hatalar için hemen fırlat
                    raise e
            
            # Bu noktaya gelmemeli ama güvenlik için
            raise last_exception
            
        return wrapper
    return decorator

def safe_db_query(query_func, default_value=None):
    """Güvenli veritabanı sorgusu"""
    try:
        return query_func()
    except (OperationalError, DisconnectionError) as e:
        print(f"❌ Veritabanı sorgu hatası: {e}")
        
        # Bağlantıyı temizle
        try:
            db.session.rollback()
            db.session.close()
        except:
            pass
            
        return default_value
    except Exception as e:
        print(f"❌ Genel sorgu hatası: {e}")
        return default_value

def check_database_health():
    """Veritabanı sağlığını kontrol et"""
    try:
        # Basit bir sorgu çalıştır
        result = db.session.execute("SELECT 1").fetchone()
        return True, "Veritabanı sağlıklı"
    except Exception as e:
        return False, f"Veritabanı sorunu: {e}"