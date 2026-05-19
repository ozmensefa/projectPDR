# -*- coding: utf-8 -*-
from faster_whisper import WhisperModel
from datetime import datetime, timedelta
import os
import pathlib

class TextService:
    def __init__(self):
        # Model ve cache dizini
        self.model_dir = pathlib.Path(__file__).parent.parent / "models" / "faster-whisper-large-v3"
        
        # CPU thread sayısını algıla
        cpu_threads = os.cpu_count() or 4
        # Tüm çekirdekleri kullanma, sistemin yarısını bırak
        self.cpu_threads = max(2, cpu_threads // 2)
        
        print(f"TextService başlatılıyor...")
        print(f"  • CPU threads: {self.cpu_threads}/{cpu_threads}")
        print(f"  • Model dizini: {self.model_dir}")
        
        try:
            print("faster-whisper large-v3 modeli yükleniyor...")
            print("  ⚠️  İlk çalıştırmada model indirme ~3 GB sürebilir!")
            
            self.model = WhisperModel(
                "large-v3",
                device="cpu",
                compute_type="int8",
                download_root=str(self.model_dir),
                cpu_threads=self.cpu_threads,
            )
            
            print("✅ faster-whisper large-v3 modeli yüklendi (CPU, int8)")
            
        except Exception as e:
            print(f"❌ faster-whisper yükleme hatası: {e}")
            print("🔄 Fallback: openai-whisper medium modeline geçiliyor...")
            self._load_fallback_model()
    
    def _load_fallback_model(self):
        """Eski openai-whisper medium modeline fallback"""
        try:
            import whisper
            import torch
            
            model_file = pathlib.Path(__file__).parent.parent / "models" / "whisper" / "medium" / "model.pt"
            has_custom_model = model_file.exists()
            
            self.model = whisper.load_model("medium", device="cpu")
            
            if has_custom_model:
                try:
                    checkpoint = torch.load(str(model_file), map_location="cpu")
                    if 'model_state_dict' in checkpoint:
                        self.model.load_state_dict(checkpoint['model_state_dict'])
                    else:
                        self.model.load_state_dict(checkpoint)
                    print("✅ Fallback: Özel fine-tune whisper medium modeli yüklendi")
                except Exception as e:
                    print(f"⚠️ Özel model yüklenemedi, standart medium kullanılacak: {e}")
            
            self._use_fallback = True
            print("✅ Fallback: openai-whisper medium modeli yüklendi (CPU)")
        except Exception as e2:
            raise Exception(f"Hiçbir model yüklenemedi: {e2}")
    
    def analyze(self, audio_path):
        try:
            print(f"Ses dosyası analiz ediliyor: {audio_path}")
            
            if hasattr(self, '_use_fallback') and self._use_fallback:
                return self._analyze_with_openai_whisper(audio_path)
            
            return self._analyze_with_faster_whisper(audio_path)
            
        except Exception as e:
            raise Exception(f"Metin analizi hatası: {str(e)}")
    
    def _analyze_with_faster_whisper(self, audio_path):
        """faster-whisper ile analiz"""
        print("🚀 faster-whisper large-v3 ile transkripsiyon başlıyor...")
        start_time = datetime.now()
        
        segments_gen, info = self.model.transcribe(
            audio_path,
            language="tr",
            task="transcribe",
            beam_size=5,
            best_of=5,
            patience=1.0,
            length_penalty=1.0,
            temperature=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            no_speech_threshold=0.6,
            condition_on_previous_text=False,
            initial_prompt="Bu bir psikolojik danışmanlık oturumunun video kaydıdır.",
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=400,
            ),
        )
        
        # Generator'ı listeye çevir (faster-whisper lazy evaluation yapar)
        segments_list = list(segments_gen)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"✅ faster-whisper ile işlem tamamlandı: {processing_time:.2f} saniye")
        print(f"  • Algılanan dil: {info.language} (olasılık: {info.language_probability:.2%})")
        print(f"  • Toplam süre: {info.duration:.1f} saniye")
        print(f"  • Segment sayısı: {len(segments_list)}")
        
        # faster-whisper Segment nesnelerini dict formatına dönüştür
        # Mevcut _format_analysis ile uyumlu olması için
        result = {
            "segments": [],
            "language": info.language,
        }
        
        for seg in segments_list:
            segment_dict = {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
                "avg_logprob": seg.avg_logprob,
            }
            
            # Kelime zaman damgaları varsa ekle
            if seg.words:
                segment_dict["words"] = [
                    {
                        "word": w.word,
                        "start": w.start,
                        "end": w.end,
                        "probability": w.probability,
                    }
                    for w in seg.words
                ]
            
            result["segments"].append(segment_dict)
        
        return self._format_analysis(result)
    
    def _analyze_with_openai_whisper(self, audio_path):
        """Fallback: openai-whisper ile analiz (mevcut mantık)"""
        print("💻 openai-whisper medium ile transkripsiyon başlıyor (fallback)...")
        start_time = datetime.now()
        
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
            "no_speech_threshold": 0.6,
            "word_timestamps": False,
            "fp16": False,
            "beam_size": 1,
        }
        
        result = self.model.transcribe(audio_path, **transcribe_options)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        print(f"İşlem tamamlandı (fallback): {processing_time:.2f} saniye")
        
        return self._format_analysis(result)

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
            
            # Güven skoru hesaplama - avg_logprob değerini kullan
            if 'avg_logprob' in segment:
                logprob = segment['avg_logprob']
                confidence = max(0.0, min(1.0, (logprob + 5.0) / 5.0))
                confidence_source = "logprob"
            elif 'confidence' in segment:
                confidence = segment['confidence']
                confidence_source = "direct"
            else:
                text_length = len(segment['text'].strip())
                if text_length > 10:
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