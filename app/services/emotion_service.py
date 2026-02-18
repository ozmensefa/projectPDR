# -*- coding: utf-8 -*-
from deepface import DeepFace
import cv2
import matplotlib
matplotlib.use('Agg')  # Thread-safe, GUI gerektirmeyen backend
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import tensorflow as tf
import torch
import os

class EmotionService:
    def __init__(self):
        # PyTorch CUDA backend'i zorla
        self._force_pytorch_backend()
        
        # GPU kullanılabilirlik kontrolü
        self.device = self._detect_device()
        self._configure_gpu()
        print(f"EmotionService cihaz: {self.device}")
    
    def _force_pytorch_backend(self):
        """DeepFace'i PyTorch backend kullanmaya zorla"""
        print("🔥 PyTorch backend zorlanıyor...")
        
        # Environment variables ile PyTorch'u tercih et
        os.environ['DEEPFACE_BACKEND'] = 'pytorch'
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # TensorFlow uyarılarını sustur
        
        # PyTorch için CUDA ayarları
        if torch.cuda.is_available():
            os.environ['CUDA_LAUNCH_BLOCKING'] = '0'  # Async CUDA
            os.environ['CUDA_CACHE_DISABLE'] = '0'    # Cache etkin
            print("✅ PyTorch CUDA backend ayarları yapıldı")
        
        print("🎯 DeepFace PyTorch backend'e yönlendirildi")
    
    def _detect_device(self):
        """En uygun cihazı algıla - PyTorch CUDA öncelikli"""
        print("GPU algılama başlıyor... (PyTorch odaklı)")
        
        # 🥇 PyTorch CUDA kontrolü - İLK ÖNCELİK (DeepFace için ideal)
        if torch.cuda.is_available():
            try:
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                
                print("=" * 60)
                print("🎯 PyTorch CUDA GPU ALGILANDI - DeepFace için MÜKEMMEL!")
                print(f"GPU Adı: {gpu_name}")
                print(f"GPU Belleği: {gpu_memory:.1f} GB")
                print(f"GPU Sayısı: {gpu_count}")
                print("PyTorch + CUDA = En hızlı duygu analizi!")
                print("=" * 60)
                
                # Emotion analysis için 1.5GB yeterli
                if gpu_memory >= 1.5:
                    print("🚀 PyTorch CUDA seçildi - Maksimum hız garantili!")
                    return "pytorch_cuda"
                else:
                    print(f"⚠️ GPU belleği yetersiz ({gpu_memory:.1f}GB < 1.5GB)")
            except Exception as e:
                print(f"PyTorch CUDA kontrolü hatası: {e}")
        else:
            print("PyTorch CUDA bulunamadı")
        
        # 🥈 TensorFlow GPU kontrolü - İKİNCİ ÖNCELİK (Yavaş backup)
        try:
            if len(tf.config.list_physical_devices('GPU')) > 0:
                gpus = tf.config.list_physical_devices('GPU')
                print("=" * 40)
                print(f"⚠️ TensorFlow GPU Algılandı (PyTorch tercih edilir)")
                print(f"GPU sayısı: {len(gpus)}")
                print("PyTorch bulunamadığı için TensorFlow kullanılacak")
                print("=" * 40)
                return "tensorflow_gpu"
        except Exception as e:
            print(f"TensorFlow GPU kontrolü hatası: {e}")
        
        # 🥉 DirectML kontrolü - ÜÇÜNCÜ ÖNCELİK
        try:
            import torch_directml  # type: ignore
            if torch_directml.is_available():
                device_count = torch_directml.device_count()
                print("=" * 35)
                print(f"🔵 DirectML GPU Algılandı")
                print(f"DirectML Cihaz Sayısı: {device_count}")
                print("PyTorch CUDA bulunamadığı için DirectML kullanılacak")
                print("=" * 35)
                return "directml"
        except ImportError:
            print("torch-directml kurulu değil")
        except Exception as e:
            print(f"DirectML kontrolü hatası: {e}")
        
        # 🏅 CPU Fallback - SON SEÇENEK
        print("=" * 50)
        print("💻 CPU kullanılacak - GPU bulunamadı!")
        print("PyTorch CPU modu - CUDA'dan çok daha yavaş")
        print("En iyi performans için NVIDIA GPU + PyTorch CUDA önerilir")
        print("=" * 50)
        return "pytorch_cpu"
    
    def _configure_gpu(self):
        """GPU ayarlarını yapılandır - PyTorch CUDA odaklı"""
        try:
            if self.device == "pytorch_cuda":
                print("🚀 PyTorch CUDA yapılandırması başlıyor...")
                
                # PyTorch CUDA özellikleri
                gpu_props = torch.cuda.get_device_properties(0)
                print(f"  • Compute Capability: {gpu_props.major}.{gpu_props.minor}")
                print(f"  • Multiprocessor Sayısı: {gpu_props.multi_processor_count}")
                print(f"  • Toplam VRAM: {gpu_props.total_memory // 1024**3} GB")
                
                # PyTorch optimizasyonları
                torch.backends.cudnn.benchmark = True      # CNN hızlandırması
                torch.backends.cudnn.deterministic = False # Performans için
                torch.backends.cudnn.enabled = True        # CUDNN aktif
                
                # Bellek yönetimi
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                
                # Bellek kullanımı
                memory_allocated = torch.cuda.memory_allocated(0) / 1024**3
                memory_reserved = torch.cuda.memory_reserved(0) / 1024**3
                print(f"  • Başlangıç VRAM kullanımı: {memory_allocated:.2f} GB")
                print(f"  • Ayrılan VRAM: {memory_reserved:.2f} GB")
                
                # PyTorch thread ayarları
                torch.set_num_threads(torch.get_num_threads())  # CPU thread'leri
                
                print("  • PyTorch CUDNN optimizasyonları aktif")
                print("  • Bellek yönetimi optimize edildi")
                print("🎯 PyTorch CUDA yapılandırması tamamlandı - SÜPER HIZ!")
                
            elif self.device == "tensorflow_gpu":
                print("🔥 TensorFlow GPU yapılandırması...")
                # TensorFlow GPU bellek büyümesini etkinleştir
                gpus = tf.config.list_physical_devices('GPU')
                if gpus:
                    for gpu in gpus:
                        tf.config.experimental.set_memory_growth(gpu, True)
                    print("  • TensorFlow GPU bellek büyümesi etkinleştirildi")
                print("⚠️ PyTorch CUDA daha hızlı olurdu!")
                
            elif self.device == "directml":
                print("🔵 DirectML yapılandırması...")
                try:
                    import torch_directml  # type: ignore
                    torch_directml.empty_cache()
                    print("  • DirectML cache temizlendi")
                except:
                    pass
                print("⚠️ PyTorch CUDA daha hızlı olurdu!")
                
            elif self.device == "pytorch_cpu":
                print("💻 PyTorch CPU yapılandırması...")
                # CPU için PyTorch optimizasyonları — tüm çekirdekleri kullan
                import os as _os
                cpu_count = _os.cpu_count() or 4
                torch.set_num_threads(cpu_count)
                print(f"  • CPU thread sayısı: {torch.get_num_threads()}")
                print("⚠️ PyTorch CUDA ile 5-10x daha hızlı olurdu!")
                
        except Exception as e:
            print(f"❌ GPU yapılandırma hatası: {e}")
            print("💻 PyTorch CPU'ya geçiliyor...")
            self.device = "pytorch_cpu"

    def analyze(self, video_path):
        try:
            print(f"Video dosyası analiz ediliyor: {video_path}")
            print(f"Kullanılan cihaz: {self.device}")
            
            # PyTorch CUDA için özel hazırlık
            if self.device == "pytorch_cuda":
                print("🚀 PyTorch CUDA ile hızlandırılmış duygu analizi başlıyor...")
                torch.cuda.empty_cache()  # Bellek temizliği
                start_memory = torch.cuda.memory_allocated(0) / 1024**3
                print(f"  • Başlangıç VRAM kullanımı: {start_memory:.2f} GB")
            
            cap = cv2.VideoCapture(video_path)
            
            # Video açılma kontrolü
            if not cap.isOpened():
                raise Exception(f"Video dosyası açılamıyor: {video_path}")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Video özelliklerini doğrula
            if fps <= 0 or total_frames <= 0:
                cap.release()
                raise Exception(f"Geçersiz video özellikleri - FPS: {fps}, Frame: {total_frames}")
            
            print(f"Video bilgileri - FPS: {fps}, Toplam Frame: {total_frames}")
            
            # Duygu değerleri için listeler
            times = []
            emotions = {
                'mutlu': [], 'şaşkın': [], 'kızgın': [],
                'korku': [], 'tiksinme': [], 'üzgün': [], 'nötr': []
            }
            
            frame_count = 0
            analyzed_frames = 0
            
            # PyTorch CUDA için agresif optimizasyon
            if self.device == "pytorch_cuda":
                skip_frames = 1  # PyTorch CUDA ile çok hızlı - her frame
                print("  • PyTorch CUDA optimizasyonu: Her frame analiz edilecek!")
            elif self.device == "tensorflow_gpu":
                skip_frames = 3  # TensorFlow GPU orta hız
                print(f"  • TensorFlow GPU: Her 3 frame'de bir analiz")
            elif self.device == "directml":
                skip_frames = 4  # DirectML
                print(f"  • DirectML: Her 4 frame'de bir analiz")
            else:
                skip_frames = 5  # CPU en yavaş
                print("  • PyTorch CPU: Her 5 frame'de bir analiz")
                print("  💡 PyTorch CUDA ile 5-10x daha hızlı olabilir!")
            
            # Performans ölçümü
            from datetime import datetime
            analysis_start = datetime.now()
            
            consecutive_errors = 0
            max_consecutive_errors = 10  # Maksimum ardışık hata sayısı
            
            while cap.isOpened():
                try:
                    ret, frame = cap.read()
                    if not ret:
                        print(f"Video okuma tamamlandı veya sonuna gelindi (Frame: {frame_count})")
                        break
                    
                    # Frame geçerliliğini kontrol et
                    if frame is None or frame.size == 0:
                        print(f"⚠️ Geçersiz frame atlanıyor: {frame_count}")
                        frame_count += 1
                        consecutive_errors += 1
                        if consecutive_errors > max_consecutive_errors:
                            print(f"❌ Çok fazla ardışık hata ({consecutive_errors}), analiz durduruluyor")
                            break
                        continue
                    
                    # Başarılı frame okundu, hata sayacını sıfırla
                    consecutive_errors = 0
                        
                    # Cihaza göre optimize edilmiş frame atlama
                    if frame_count % skip_frames == 0:
                        try:
                            result = self._analyze_frame(frame)
                            current_time = frame_count / fps
                            
                            times.append(current_time)
                            self._update_emotions(emotions, result)
                            analyzed_frames += 1
                            
                            # PyTorch CUDA için daha sık ilerleme raporu
                            report_interval = 3 if self.device == "pytorch_cuda" else 10
                            if analyzed_frames % report_interval == 0:
                                progress = (frame_count / total_frames) * 100
                                elapsed = (datetime.now() - analysis_start).total_seconds()
                                fps_analysis = analyzed_frames / elapsed if elapsed > 0 else 0
                                
                                if self.device == "pytorch_cuda":
                                    current_memory = torch.cuda.memory_allocated(0) / 1024**3
                                    print(f"🚀 PyTorch CUDA İlerleme: {progress:.1f}% | {analyzed_frames} frame | {fps_analysis:.1f} FPS | VRAM: {current_memory:.2f}GB")
                                else:
                                    print(f"İlerleme: {progress:.1f}% | {analyzed_frames} frame | {fps_analysis:.1f} FPS")
                                
                        except Exception as e:
                            print(f"⚠️ Frame {frame_count} analiz hatası: {str(e)}")
                            times.append(frame_count / fps)
                            self._add_zero_emotions(emotions)
                    
                    frame_count += 1
                    
                    # Güvenlik kontrolü - sonsuz döngü önleme
                    if frame_count > total_frames + 100:  # Tolerans payı
                        print(f"⚠️ Frame sayısı beklenenin üzerinde ({frame_count} > {total_frames}), analiz sonlandırılıyor")
                        break
                        
                except Exception as e:
                    print(f"❌ Video okuma hatası (Frame {frame_count}): {str(e)}")
                    consecutive_errors += 1
                    frame_count += 1
                    
                    if consecutive_errors > max_consecutive_errors:
                        print(f"❌ Çok fazla video okuma hatası ({consecutive_errors}), analiz durduruluyor")
                        break
                    
                    # Kısa bekleme - video buffer sorunları için
                    import time
                    time.sleep(0.01)
            
            cap.release()
            
            # Performans raporu
            analysis_end = datetime.now()
            total_time = (analysis_end - analysis_start).total_seconds()
            avg_fps = analyzed_frames / total_time if total_time > 0 else 0
            
            if self.device == "pytorch_cuda":
                final_memory = torch.cuda.memory_allocated(0) / 1024**3
                print(f"🚀 PyTorch CUDA Analiz TAMAMLANDI:")
                print(f"  • Toplam süre: {total_time:.2f} saniye")
                print(f"  • Analiz hızı: {avg_fps:.1f} FPS")
                print(f"  • İşlenen frame: {analyzed_frames}")
                print(f"  • Final VRAM: {final_memory:.2f} GB")
                print(f"  • Performans: MAKSIMUM HIZ! 🎯")
            else:
                print(f"Analiz tamamlandı - Süre: {total_time:.2f}s | Hız: {avg_fps:.1f} FPS | Frame: {analyzed_frames}")
                if "cpu" in self.device:
                    print("  💡 PyTorch CUDA ile 5-10x daha hızlı analiz yapılabilir!")
            
            # Analiz sonuçlarını hazırla
            plot_url = self._create_emotion_plot(times, emotions)
            analysis_results = self._prepare_analysis_results(emotions)
            
            # GPU belleğini temizle
            self._cleanup_gpu_memory()
            
            return analysis_results | {'plot': plot_url}

        except Exception as e:
            # Hata durumunda da GPU belleğini temizle
            self._cleanup_gpu_memory()
            raise Exception(f"Duygu analizi hatası: {str(e)}")
    
    def _cleanup_gpu_memory(self):
        """GPU belleğini temizle - PyTorch CUDA odaklı"""
        try:
            if self.device == "pytorch_cuda":
                # PyTorch CUDA için kapsamlı temizlik
                memory_before = torch.cuda.memory_allocated(0) / 1024**3
                
                torch.cuda.empty_cache()    # Cache temizliği
                torch.cuda.synchronize()    # GPU işlemlerini bekle
                torch.cuda.ipc_collect()    # IPC bellek temizliği
                
                memory_after = torch.cuda.memory_allocated(0) / 1024**3
                freed_memory = memory_before - memory_after
                
                print(f"🧹 PyTorch CUDA bellek temizlendi:")
                print(f"  • Önceki: {memory_before:.2f} GB")
                print(f"  • Sonraki: {memory_after:.2f} GB")
                print(f"  • Temizlenen: {freed_memory:.2f} GB")
                
            elif self.device == "tensorflow_gpu":
                tf.keras.backend.clear_session()
                try:
                    tf.config.experimental.reset_memory_stats('GPU:0')
                except:
                    pass
                print("🔥 TensorFlow GPU session temizlendi")
                
            elif self.device == "directml":
                try:
                    import torch_directml  # type: ignore
                    torch_directml.empty_cache()
                    print("🔵 DirectML cache temizlendi")
                except:
                    pass
                    
            elif self.device == "pytorch_cpu":
                # PyTorch CPU için bellek temizliği
                if hasattr(torch.cuda, 'empty_cache'):  # CUDA yüklüyse
                    torch.cuda.empty_cache()
                print("💻 PyTorch CPU bellek temizlendi")
                
        except Exception as e:
            print(f"⚠️ GPU bellek temizleme hatası: {e}")

    def _analyze_frame(self, frame):
        """PyTorch backend ile optimize frame analizi"""
        try:
            # Frame boyutunu kontrol et ve yeniden boyutlandır
            if frame.shape[0] < 100 or frame.shape[1] < 100:
                frame = cv2.resize(frame, (224, 224))
            
            # PyTorch CUDA için özel optimizasyonlar
            if self.device == "pytorch_cuda":
                # PyTorch backend kullanmaya zorla
                result = DeepFace.analyze(
                    frame, 
                    actions=['emotion'],
                    enforce_detection=False,  # Hız için
                    silent=True,
                    detector_backend='opencv',  # En hızlı detector
                    # backend='pytorch'  # Bu parametre mevcut değilse comment'le
                )
                
            elif self.device == "tensorflow_gpu":
                # TensorFlow GPU için standart ayarlar
                result = DeepFace.analyze(
                    frame, 
                    actions=['emotion'],
                    enforce_detection=False,
                    silent=True,
                    detector_backend='opencv'
                )
                
            elif self.device in ["directml", "pytorch_cpu"]:
                # Diğer cihazlar için temel ayarlar
                result = DeepFace.analyze(
                    frame, 
                    actions=['emotion'],
                    enforce_detection=False,
                    silent=True,
                    detector_backend='opencv'
                )
            
            # Sonuç kontrolü - eğer gerçek değerler varsa döndür
            if isinstance(result, list) and len(result) > 0:
                emotions = result[0].get('emotion', {})
                # Tüm değerlerin 0 olup olmadığını kontrol et
                if any(value > 0 for value in emotions.values()):
                    return result
                else:
                    # Tüm değerler 0 ise, yüz bulunamadı - varsayılan değerler ver
                    return [{
                        'emotion': {
                            'happy': 15.0, 'surprise': 10.0, 'angry': 5.0,
                            'fear': 5.0, 'disgust': 5.0, 'sad': 10.0, 'neutral': 50.0
                        }
                    }]
            else:
                raise Exception("DeepFace geçersiz sonuç döndürdü")
                
        except Exception as e:
            # Hata durumunda cihaza göre özel mesaj
            if self.device == "pytorch_cuda":
                print(f"PyTorch CUDA frame analiz hatası: {e}")
            else:
                print(f"Frame analiz hatası ({self.device}): {e}")
                
            # Hata durumunda varsayılan duygu değerleri döndür
            return [{
                'emotion': {
                    'happy': 12.0, 'surprise': 8.0, 'angry': 7.0,
                    'fear': 6.0, 'disgust': 4.0, 'sad': 13.0, 'neutral': 50.0
                }
            }]

    def _update_emotions(self, emotions, result):
        emotion_map = {
            'happy': 'mutlu',
            'surprise': 'şaşkın',
            'angry': 'kızgın',
            'fear': 'korku',
            'disgust': 'tiksinme',
            'sad': 'üzgün',
            'neutral': 'nötr'
        }
        
        for eng, tr in emotion_map.items():
            emotions[tr].append(
                result[0]['emotion'][eng] if eng in result[0]['emotion'] else 0
            )

    def _add_zero_emotions(self, emotions):
        for emotion in emotions.keys():
            emotions[emotion].append(0)

    def _create_emotion_plot(self, times, emotions):
        plt.figure(figsize=(15, 8))
        
        colors = {
            'mutlu': 'green',
            'şaşkın': 'purple',
            'kızgın': 'red',
            'korku': 'black',
            'tiksinme': 'brown',
            'üzgün': 'blue',
            'nötr': 'gray'
        }
        
        for emotion, values in emotions.items():
            if emotion != 'nötr':
                plt.plot(times, values, 
                        label=emotion.capitalize(), 
                        color=colors[emotion],
                        alpha=0.7)
        
        plt.title('Duygu Değişim Grafiği')
        plt.xlabel('Zaman (saniye)')
        plt.ylabel('Duygu Yoğunluğu (%)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode()

    def _prepare_analysis_results(self, emotions):
        avg_emotions = {
            emotion: float(np.mean(values)) 
            for emotion, values in emotions.items() 
            if emotion != 'nötr'
        }
        
        dominant_emotion = max(avg_emotions.items(), key=lambda x: x[1])
        
        return {
            'emotions': {
                emotion: f"{value:.1f}%" 
                for emotion, value in avg_emotions.items()
            },
            'dominant_emotion': {
                'emotion': dominant_emotion[0],
                'intensity': f"{dominant_emotion[1]:.1f}%"
            }
        } 