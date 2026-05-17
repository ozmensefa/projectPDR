# -*- coding: utf-8 -*-
import whisper
from datetime import datetime, timedelta
import os
import pathlib
import torch

class TextService:
    def __init__(self):
        # GPU kullanılabilirlik kontrolü
        self.device = self._detect_device()
        print(f"TextService cihaz: {self.device}")
        
        # Özel fine-tune model dosyasının yolu (opsiyonel)
        self.model_file = pathlib.Path(__file__).parent.parent / "models" / "whisper" / "medium" / "model.pt"
        self.has_custom_model = self.model_file.exists()
        
        if self.has_custom_model:
            print("Özel fine-tune Whisper modeli bulundu, yükleniyor...")
        else:
            print("Özel model bulunamadı, standart Whisper 'medium' modeli kullanılacak...")
            print("(İlk çalıştırmada model otomatik indirilecek)")
        
        print("Whisper modeli yükleniyor...")
        
        try:
            device_str = "cuda" if self.device == "cuda" else "cpu"
            
            if self.device == "cuda":
                print("🚀 NVIDIA CUDA ile model yükleniyor!")
                torch.cuda.empty_cache()
            else:
                print("💻 CPU ile model yükleniyor...")
            
            # Önce standart modeli yükle
            self.model = whisper.load_model("medium", device=device_str)
            
            # Özel checkpoint varsa üzerine yükle
            if self.has_custom_model:
                try:
                    checkpoint = torch.load(str(self.model_file), map_location=device_str)
                    if 'model_state_dict' in checkpoint:
                        self.model.load_state_dict(checkpoint['model_state_dict'])
                    else:
                        self.model.load_state_dict(checkpoint)
                    print("✅ Özel fine-tune model yüklendi!")
                except Exception as e:
                    print(f"⚠️ Özel model yüklenemedi, standart model kullanılacak: {e}")
            
            print(f"✅ Whisper model yükleme tamamlandı ({device_str})")
                    
        except Exception as e:
            print(f"Model yükleme hatası, CPU fallback deneniyor: {e}")
            try:
                self.device = "cpu"
                self.model = whisper.load_model("medium", device="cpu")
                print("✅ CPU fallback ile model yüklendi")
            except Exception as e2:
                raise Exception(f"Whisper modeli yüklenemedi: {e2}")
    
    def _detect_device(self):
        """En uygun cihazı algıla - CUDA öncelikli"""
        print("GPU algılama başlıyor...")
        
        # 🥇 NVIDIA CUDA kontrolü - İLK ÖNCELİK
        if torch.cuda.is_available():
            try:
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                
                print("=" * 50)
                print("🎯 NVIDIA CUDA GPU ALGILANDI - ÖNCE TERCIH!")
                print(f"GPU Adı: {gpu_name}")
                print(f"GPU Belleği: {gpu_memory:.1f} GB")
                print(f"GPU Sayısı: {gpu_count}")
                print("=" * 50)
                
                # En az 2GB GPU belleği gerekli (daha düşük threshold)
                if gpu_memory >= 2.0:
                    print("✅ NVIDIA CUDA seçildi - En iyi performans için!")
                    return "cuda"
                else:
                    print(f"⚠️ GPU belleği yetersiz ({gpu_memory:.1f}GB < 2GB), diğer seçenekler kontrol ediliyor...")
            except Exception as e:
                print(f"CUDA kontrolü hatası: {e}")
        else:
            print("NVIDIA CUDA bulunamadı veya kullanılamıyor")
        
        # 🥈 AMD ROCm kontrolü - İKİNCİ ÖNCELİK
        try:
            if hasattr(torch, 'hip') and torch.hip.is_available():
                gpu_count = torch.hip.device_count()
                print(f"🔴 AMD GPU Algılandı (ROCm)")
                print(f"GPU Sayısı: {gpu_count}")
                print("✅ AMD ROCm seçildi")
                return "hip"
        except Exception as e:
            print(f"AMD ROCm kontrolü hatası: {e}")
        
        # 🥉 Intel GPU / OpenCL kontrolü - ÜÇÜNCÜ ÖNCELİK
        try:
            import pyopencl as cl # type: ignore
            platforms = cl.get_platforms()
            gpu_devices = []
            
            for platform in platforms:
                devices = platform.get_devices(device_type=cl.device_type.GPU)
                gpu_devices.extend(devices)
            
            if gpu_devices:
                for i, device in enumerate(gpu_devices):
                    device_name = device.name.strip()
                    global_mem = device.global_mem_size / 1024**3
                    print(f"🔵 OpenCL GPU {i} Algılandı: {device_name}")
                    print(f"GPU Belleği: {global_mem:.1f} GB")
                    
                    # Intel Arc, AMD Radeon vb. için - Whisper OpenCL desteği sınırlı
                    print("⚠️ OpenCL GPU algılandı ancak Whisper ile uyumsuzluk nedeniyle CPU kullanılacak")
            
        except ImportError:
            print("PyOpenCL kurulu değil, OpenCL GPU desteği yok")
        except Exception as e:
            print(f"OpenCL GPU kontrolü hatası: {e}")
        
        # 🔄 CPU Fallback - SON SEÇENEK
        print("=" * 50)
        print("💻 CPU kullanılacak - CUDA bulunamadı!")
        print("En iyi performans için NVIDIA GPU + CUDA önerilir")
        print("=" * 50)
        return "cpu"

    def analyze(self, audio_path):
        try:
            print(f"Ses dosyası analiz ediliyor: {audio_path}")
            print(f"Kullanılan cihaz: {self.device}")
            
            # CUDA için özel hazırlık
            if self.device == "cuda":
                print("🚀 CUDA ile hızlandırılmış analiz başlıyor...")
                torch.cuda.empty_cache()  # Bellek temizliği
                print(f"  • Mevcut VRAM: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
            
            # GPU/CPU'ya göre optimize edilmiş ayarlar
            transcribe_options = {
                "language": "tr",
                "task": "transcribe",
                "verbose": True,
                "condition_on_previous_text": False,
                "initial_prompt": "Bu bir video konuşma transkripsiyonudur.",
                "compression_ratio_threshold": 2.4,
                "temperature": 0,
                "best_of": 1,
                "logprob_threshold": -1.0,
                "no_speech_threshold": 0.6
            }
            
            # CUDA için özel optimizasyonlar - EN İYİ AYARLAR
            if self.device == "cuda":
                transcribe_options.update({
                    "word_timestamps": True,  # Kelime zamanlaması
                    "fp16": True,  # Yarı precision - 2x hız artışı
                    "beam_size": 5,  # Daha iyi kalite
                    "best_of": 5,  # En iyi sonuç seçimi
                    "temperature": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],  # Çoklu sıcaklık
                    "patience": 1.0,  # Beam search patience
                    "length_penalty": 1.0,  # Uzunluk cezası
                    "suppress_tokens": "-1",  # Token bastırma
                    "condition_on_previous_text": False  # Önceki metne dayalı
                })
                print("  • CUDA optimize ayarları aktif - En yüksek kalite")
                
            # Diğer GPU'lar için temel ayarlar
            elif self.device in ["hip", "directml", "opencl"]:
                transcribe_options.update({
                    "word_timestamps": False,  # Uyumluluk için kapalı
                    "fp16": False,  # Kararlılık için FP32
                    "beam_size": 1,  # Hız için basit
                    "best_of": 1
                })
                print(f"  • {self.device.upper()} temel ayarları aktif")
                
            # CPU için optimizasyon
            else:
                transcribe_options.update({
                    "word_timestamps": False,
                    "fp16": False,
                    "beam_size": 1,
                    "best_of": 1,
                    "temperature": 0  # Deterministik sonuç
                })
                print("  • CPU ayarları aktif - CUDA önerilir!")
            
            # Transkripsiyon işlemi
            print("Transkripsiyon başlıyor...")
            start_time = datetime.now()
            
            result = self.model.transcribe(audio_path, **transcribe_options)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # CUDA için performans raporu
            if self.device == "cuda":
                print(f"🎯 CUDA ile işlem tamamlandı: {processing_time:.2f} saniye")
                print(f"  • İşlem sonrası VRAM: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
                torch.cuda.empty_cache()  # İşlem sonrası temizlik
            else:
                print(f"İşlem tamamlandı: {processing_time:.2f} saniye")
                if self.device == "cpu":
                    print("  💡 CUDA ile 3-5x daha hızlı olabilir!")

            # Sonucu formatla
            formatted_result = self._format_analysis(result)
            
            return formatted_result

        except Exception as e:
            raise Exception(f"Metin analizi hatası: {str(e)}")

    def _format_analysis(self, result):
        formatted_text = "Konuşma Analizi:\n\n"
        
        # Metadata ekle
        formatted_text += "Analiz Bilgileri:\n"
        formatted_text += f"Tarih: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        
        # Segment kontrolü
        if result.get('segments') and len(result['segments']) > 0:
            total_duration = result['segments'][-1]['end']
            formatted_text += f"Toplam Süre: {str(timedelta(seconds=int(total_duration)))}\n"
            formatted_text += f"Segment Sayısı: {len(result['segments'])}\n"
        else:
            formatted_text += "Toplam Süre: Bilinmiyor\n"
            formatted_text += "Segment Sayısı: 0 (Ses algılanmadı)\n"
            total_duration = 0
            
        formatted_text += "=" * 50 + "\n\n"

        # Segmentleri detaylı bilgilerle ekle
        formatted_text += "Detaylı Transkripsiyon:\n\n"
        
        total_words = 0
        total_confidence = 0
        
        # Segment kontrolü
        if not result.get('segments') or len(result['segments']) == 0:
            formatted_text += "Hiçbir konuşma segmenti algılanmadı.\n"
            formatted_text += "Bu durum sessiz video, çok düşük ses seviyesi veya tanınmayan dil nedeniyle olabilir.\n\n"
            
            return {
                "text": formatted_text,
                "raw_analysis": {
                    "metadata": {
                        "tarih": datetime.now().strftime('%d/%m/%Y %H:%M'),
                        "toplam_sure": "0:00:00",
                        "segment_sayisi": 0
                    },
                    "segments": [],
                    "istatistikler": {
                        "toplam_kelime": 0,
                        "ortalama_konusma_hizi": "0.0",
                        "ortalama_guven": "0.00%",
                        "toplam_segment": 0
                    }
                }
            }

        for i, segment in enumerate(result["segments"], 1):
            start_time = str(timedelta(seconds=int(segment['start']))).split('.')[0]
            end_time = str(timedelta(seconds=int(segment['end']))).split('.')[0]
            duration = segment['end'] - segment['start']
            
            formatted_text += f"Segment {i}:\n"
            formatted_text += f"Zaman: [{start_time} - {end_time}] ({duration:.1f} sn)\n"
            formatted_text += f"Metin: {segment['text'].strip()}\n"
            
            # Word count hesaplama (words array varsa kullan, yoksa text'ten hesapla)
            if 'words' in segment and segment['words']:
                words = len(segment['words'])
                words_per_second = words / duration if duration > 0 else 0
                formatted_text += f"Konuşma Hızı: {words_per_second:.1f} kelime/saniye\n"
            else:
                # Word timestamps yoksa, text'ten kelime sayısını hesapla
                words = len(segment['text'].strip().split())
                words_per_second = words / duration if duration > 0 else 0
                formatted_text += f"Konuşma Hızı: {words_per_second:.1f} kelime/saniye (tahmini)\n"
            
            total_words += words
            
            # Güven skoru hesaplama - Whisper'ın avg_logprob değerini kullan
            if 'avg_logprob' in segment:
                # avg_logprob değerini confidence'a dönüştür (0-1 arası)
                # avg_logprob genellikle -inf ile 0 arasında, daha yüksek değer daha iyi
                logprob = segment['avg_logprob']
                # Logprob'u 0-1 arası confidence'a dönüştür
                confidence = max(0.0, min(1.0, (logprob + 5.0) / 5.0))  # -5 ile 0 arası normalize et
                confidence_source = "logprob"
            elif 'confidence' in segment:
                confidence = segment['confidence']
                confidence_source = "direct"
            else:
                # Segment uzunluğu ve compression ratio'ya göre tahmini güven skoru
                text_length = len(segment['text'].strip())
                if text_length > 10:  # Uzun segment = daha güvenilir
                    confidence = 0.85
                elif text_length > 5:
                    confidence = 0.70
                else:
                    confidence = 0.50
                confidence_source = "estimated"
            
            total_confidence += confidence
            formatted_text += f"Güven Skoru: {confidence:.2%} ({confidence_source})\n"
            formatted_text += "-" * 40 + "\n"

        # İstatistikler
        avg_confidence = total_confidence / len(result['segments'])
        avg_words_per_second = total_words / total_duration if total_duration > 0 else 0
        
        formatted_text += "\nGenel İstatistikler:\n"
        formatted_text += f"Toplam Kelime Sayısı: {total_words}\n"
        formatted_text += f"Ortalama Konuşma Hızı: {avg_words_per_second:.1f} kelime/saniye\n"
        formatted_text += f"Ortalama Güven Skoru: {avg_confidence:.2%}\n"

        return {
            "text": formatted_text,
            "raw_analysis": {
                "metadata": {
                    "tarih": datetime.now().strftime('%d/%m/%Y %H:%M'),
                    "toplam_sure": str(timedelta(seconds=int(total_duration))),
                    "segment_sayisi": len(result['segments'])
                },
                "segments": result['segments'],
                "istatistikler": {
                    "toplam_kelime": total_words,
                    "ortalama_konusma_hizi": f"{avg_words_per_second:.1f}",
                    "ortalama_guven": f"{avg_confidence:.2%}",
                    "toplam_segment": len(result['segments'])
                }
            }
        } 