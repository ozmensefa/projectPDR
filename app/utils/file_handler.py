# -*- coding: utf-8 -*-
import os
import subprocess
import cv2
from app.config import Config

class FileHandler:
    def __init__(self):
        """FileHandler başlangıç ayarları"""
        self.video_folder = Config.UPLOAD_FOLDER
        self.temp_folder = Config.TEMP_FOLDER
        
        # Klasörleri oluştur
        for folder in [self.video_folder, self.temp_folder]:
            if not os.path.exists(folder):
                os.makedirs(folder)
    
    def save_temp_files(self, video_file):
        temp_video = os.path.join(Config.TEMP_FOLDER, "temp_video.mp4")
        temp_audio = os.path.join(Config.TEMP_FOLDER, "temp_audio.wav")
        
        video_file.save(temp_video)
        
        # Video dosyasını doğrula ve gerekirse onar
        if not self._validate_and_repair_video(temp_video):
            raise Exception("Video dosyası geçersiz veya onarılamıyor")
        
        self._convert_video_to_audio(temp_video, temp_audio)
        
        return temp_video, temp_audio

    def _validate_and_repair_video(self, video_path):
        """Video dosyasını doğrula ve gerekirse onar"""
        try:
            print(f"Video dosyası doğrulanıyor: {video_path}")
            
            # OpenCV ile temel doğrulama
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print("❌ Video dosyası açılamıyor, onarım deneniyor...")
                return self._repair_video(video_path)
            
            # Video özelliklerini kontrol et
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            cap.release()
            
            # Geçersiz değerler kontrolü
            if fps <= 0 or frame_count <= 0 or width <= 0 or height <= 0:
                print("❌ Video meta verileri geçersiz, onarım deneniyor...")
                return self._repair_video(video_path)
            
            print(f"✅ Video doğrulandı: {width}x{height}, {fps} FPS, {frame_count} frame")
            return True
            
        except Exception as e:
            print(f"❌ Video doğrulama hatası: {e}")
            return self._repair_video(video_path)

    def _repair_video(self, video_path):
        """Bozuk video dosyasını onar"""
        try:
            print("🔧 Video onarım işlemi başlatılıyor...")
            
            # Onarılmış video için geçici dosya
            repaired_path = video_path.replace('.mp4', '_repaired.mp4')
            
            # FFmpeg ile video onarımı - en güvenli parametreler
            repair_command = [
                'ffmpeg', '-y',
                '-fflags', '+genpts+igndts',  # Timestamp sorunlarını düzelt
                '-err_detect', 'ignore_err',   # Hataları görmezden gel
                '-i', video_path,
                '-c:v', 'libx264',            # H.264 codec
                '-preset', 'fast',            # Hızlı encoding
                '-crf', '23',                 # Kalite
                '-c:a', 'aac',                # Audio codec
                '-avoid_negative_ts', 'make_zero',  # Negatif timestamp'leri düzelt
                '-max_muxing_queue_size', '1024',   # Buffer boyutu
                repaired_path
            ]
            
            result = subprocess.run(repair_command, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(repaired_path):
                # Onarılmış dosyayı orijinalin üzerine kopyala
                if os.path.exists(video_path):
                    os.remove(video_path)
                os.rename(repaired_path, video_path)
                print("✅ Video başarıyla onarıldı!")
                return True
            else:
                print(f"❌ Video onarım başarısız: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Video onarım hatası: {e}")
            return False

    def _convert_video_to_audio(self, video_path, audio_path):
        """Geliştirilmiş ses dönüştürme - hata toleranslı"""
        try:
            print(f"Video'dan ses çıkarılıyor: {video_path} -> {audio_path}")
            
            # Önce basit dönüştürme dene
            command = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-vn',  # Video stream'i atla
                '-acodec', 'pcm_s16le',
                '-ac', '1',  # Mono
                '-ar', '48000',  # Sample rate
                '-af', 'highpass=f=200,lowpass=f=3000,volume=2',
                audio_path
            ]
            
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"⚠️ İlk deneme başarısız, alternatif yöntem deneniyor...")
                print(f"Hata: {result.stderr}")
                
                # Alternatif komut - daha toleranslı
                alt_command = [
                    'ffmpeg', '-y',
                    '-fflags', '+genpts',
                    '-err_detect', 'ignore_err',
                    '-i', video_path,
                    '-vn',
                    '-acodec', 'pcm_s16le',
                    '-ac', '1',
                    '-ar', '16000',  # Daha düşük sample rate
                    audio_path
                ]
                
                alt_result = subprocess.run(alt_command, capture_output=True, text=True)
                
                if alt_result.returncode != 0:
                    raise Exception(f'FFmpeg ses dönüştürme hatası: {alt_result.stderr}')
                else:
                    print("✅ Alternatif yöntemle ses başarıyla çıkarıldı!")
            else:
                print("✅ Ses başarıyla çıkarıldı!")
                
        except Exception as e:
            print(f"❌ Ses dönüştürme hatası: {e}")
            raise

    def cleanup_temp_files(self, file_paths):
        for path in file_paths:
            if os.path.exists(path):
                os.remove(path)

    @staticmethod
    def get_video_duration_minutes(video_path):
        """Video süresini dakika cinsinden döndürür"""
        try:
            if not video_path or not os.path.exists(video_path):
                return None
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            if fps > 0 and frame_count > 0:
                return round(frame_count / fps / 60, 1)
            return None
        except Exception:
            return None

    @staticmethod
    def estimate_analysis_time(video_duration_minutes):
        """
        Video süresine göre tahmini analiz süresini (min, max) dakika olarak döndürür.
        video_duration_minutes: Videonun süresi (dakika)
        Returns: (min_dakika, max_dakika) tuple
        """
        if video_duration_minutes is None or video_duration_minutes <= 0:
            return (10, 15)  # Varsayılan tahmin

        dur = video_duration_minutes

        # Temel süre: sabit başlangıç maliyeti + video süresine orantılı maliyet
        # Sabit maliyet: ~5 dakika (model yükleme, başlatma, AI rapor oluşturma vb.)
        # Değişken maliyet: video süresinin ~0.5x - 0.8x kadarı
        base = 5
        min_estimate = base + dur * 0.4
        max_estimate = base + dur * 0.7

        # Alt ve üst sınırlar
        min_estimate = max(5, round(min_estimate))
        max_estimate = max(min_estimate + 2, round(max_estimate))

        return (min_estimate, max_estimate)

    def save_video_file(self, video_file):
        """Sadece video dosyasını kaydeder"""
        temp_video = os.path.join(Config.TEMP_FOLDER, "temp_video.mp4")
        video_file.save(temp_video)
        return temp_video 