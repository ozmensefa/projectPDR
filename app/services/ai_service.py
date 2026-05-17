# -*- coding: utf-8 -*-
import google.generativeai as genai
from app.config import Config
import json
import os
import time

class AIService:
    def __init__(self, api_key_type='session'):
        """AIService başlatıcı
        
        Args:
            api_key_type: 'session' (oturum analizi) veya 'progress' (ilerleyiş analizi)
        """
        self.api_key_type = api_key_type
        
        # Analiz tipine göre doğru API key'i seç
        if api_key_type == 'progress':
            api_key = Config.GEMINI_API_KEY_PROGRESS
            key_label = 'İlerleyiş'
        else:
            api_key = Config.GEMINI_API_KEY_SESSION
            key_label = 'Oturum'
        
        if not api_key:
            raise ValueError(f"Gemini {key_label} API key bulunamadı. Lütfen GEMINI_API_KEY_{api_key_type.upper()} çevre değişkenini ayarlayın.")
        
        try:
            genai.configure(api_key=api_key)
            # Gemini 2.5 Flash modelini kullan (En güncel ve en hızlı model)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            print(f"✅ Gemini 2.5 Flash API ({key_label}) başarıyla yapılandırıldı. Key: {api_key[:10]}...")
        except Exception as e:
            print(f"❌ Gemini API ({key_label}) yapılandırma hatası: {str(e)}")
            raise
        
        # Finetuning verilerini yükle
        try:
            data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'pdrFinetune.jsonl')
            with open(data_path, 'r', encoding='utf-8') as f:
                self.training_data = json.load(f)
        except Exception as e:
            print(f"Finetuning verisi yüklenirken hata: {str(e)}")
            self.training_data = []

    def _get_generation_config(self, temperature=0.7):
        """Ortak generation config — output token limiti config'den okunur."""
        max_tokens = getattr(Config, 'GEMINI_MAX_OUTPUT_TOKENS', 8192)
        return {
            "temperature": temperature,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": max_tokens,
        }

    def _get_safety_settings(self):
        """Ortak safety settings — psikolojik raporlar için gevşetilmiş"""
        return [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ]

    def _generate_content_with_retry(self, prompt, temperature=0.7, max_retries=3):
        """429 (quota/rate limit) hatasında bekleyip tekrar dener."""
        last_error = None
        for attempt in range(max_retries):
            try:
                return self.model.generate_content(
                    prompt,
                    generation_config=self._get_generation_config(temperature),
                    safety_settings=self._get_safety_settings()
                ), None
            except Exception as e:
                last_error = e
                err_str = str(e)
                if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
                    wait_sec = [10, 25, 60][attempt] if attempt < 3 else 60
                    if attempt < max_retries - 1:
                        print(f"  ⚠️ API 429/rate limit, {wait_sec}s sonra tekrar denenecek (deneme {attempt + 1}/{max_retries})...")
                        time.sleep(wait_sec)
                    else:
                        raise
                else:
                    raise
        return None, last_error

    def _generate_with_continuation(self, prompt, temperature=0.7, max_continuations=2):
        """
        AI yanıtı oluşturur, kesilirse devam isteği gönderir.
        Birden fazla parçayı birleştirerek tam rapor döndürür.
        """
        full_response = ""
        current_prompt = prompt

        for attempt in range(1 + max_continuations):
            response, gen_error = self._generate_content_with_retry(current_prompt, temperature)
            if gen_error is not None:
                return None, str(gen_error)
            if response is None:
                return None, "Yanıt alınamadı"

            if not response.text:
                if attempt == 0:
                    return None, "Yanıt boş geldi"
                break

            full_response += response.text

            finish_reason = None
            if hasattr(response, 'candidates') and len(response.candidates) > 0:
                finish_reason = response.candidates[0].finish_reason

            print(f"  Parça {attempt + 1}: {len(response.text)} karakter, finish_reason: {finish_reason}")

            if finish_reason == 1 or finish_reason is None:
                break

            if finish_reason == 2:
                print(f"  ⚠️ Token limiti aşıldı, devam isteği gönderiliyor ({attempt + 1}/{max_continuations})...")
                current_prompt = (
                    f"Önceki yanıtın token limiti nedeniyle kesildi. "
                    f"Kaldığın yerden devam et. Son yazdığın metin şuydu:\n\n"
                    f"...{response.text[-500:]}\n\n"
                    f"Lütfen kaldığın yerden devam ederek raporu tamamla."
                )
            else:
                print(f"  ⚠️ Beklenmeyen finish_reason: {finish_reason}, devam edilmiyor.")
                break

        return full_response, None

    def analyze(self, data):
        try:
            client_name = data.get('client_name', 'Tanımsız')
            
            print("\n=== AI ANALİZ BAŞLADI ===")
            prompt = self._create_prompt(data)
            print(f"Prompt hazırlandı, uzunluk: {len(prompt)} karakter")
            
            full_response, error = self._generate_with_continuation(prompt, temperature=0.7)

            if error:
                print(f"Yanıt hatası: {error}")
                return {'analysis': f'AI analizi yapılamadı. {error}', 'status': 'error'}
            
            result = {
                'analysis': full_response,
                'status': 'success'
            }
            print(f"✅ Başarılı sonuç oluşturuldu (uzunluk: {len(full_response)} karakter)")
            return result
                
        except Exception as e:
            error_msg = str(e)
            print(f"AI analiz hatası: {error_msg}")
            
            if "API_KEY_INVALID" in error_msg:
                error_msg = "Geçersiz API key. Lütfen sistem yöneticisiyle iletişime geçin."
            elif "429" in error_msg or "quota" in error_msg.lower():
                error_msg = "API kotası aşıldı. Lütfen yöneticinizle iletişime geçin."
            elif "QUOTA_EXCEEDED" in error_msg or "RATE_LIMIT_EXCEEDED" in error_msg:
                error_msg = "API kullanım kotası aşıldı. Lütfen yöneticinizle iletişime geçin."
            elif "timeout" in error_msg.lower():
                error_msg = "İstek zaman aşımına uğradı. Lütfen tekrar deneyin."
            
            return {
                'analysis': f'Analiz sırasında bir hata oluştu: {error_msg}',
                'status': 'error'
            }

    def _estimate_tokens(self, text):
        """Karakter sayısından yaklaşık token sayısını tahmin eder.
        JSON formatındaki veriler (rakamlar ve noktalama) çok daha fazla token tüketir.
        Bu nedenle 1 token ≈ 1.8 karakter olarak daha güvenli bir hesaplama yapıyoruz."""
        return len(text) / 1.8

    def _downsample_body_data(self, body_data, factor):
        """Body data'yı her N. frame'i alarak küçültür.
        Her zaman ilk ve son frame korunur."""
        if not body_data or len(body_data) <= 2:
            return body_data
        # İlk ve son frame'i koru, aradakileri örnekle
        middle = body_data[1:-1]
        sampled = [middle[i] for i in range(0, len(middle), factor)]
        return [body_data[0]] + sampled + [body_data[-1]]

    def _summarize_body_data(self, body_data):
        """Body data'yı sadece istatistiksel özet olarak döndürür (son çare)."""
        if not body_data or not isinstance(body_data, list):
            return "Beden Dili Analizi: Veri bulunamadı."
        
        total_poses = sum(len(entry.get('poses', [])) for entry in body_data)
        timestamps = [entry.get('timestamp', 0) for entry in body_data]
        min_t = min(timestamps) if timestamps else 0
        max_t = max(timestamps) if timestamps else 0
        
        # Her zaman noktasındaki duruş sayısı ortalaması
        pose_counts = [len(entry.get('poses', [])) for entry in body_data]
        avg_poses = sum(pose_counts) / len(pose_counts) if pose_counts else 0
        
        summary = f"""Beden Dili Analizi Özeti:
- Toplam analiz noktası: {len(body_data)}
- Zaman aralığı: {min_t:.1f}s - {max_t:.1f}s
- Toplam tespit edilen pose: {total_poses}
- Ortalama pose/frame: {avg_poses:.1f}
- İlk frame ({min_t:.1f}s): {pose_counts[0] if pose_counts else 0} pose
- Son frame ({max_t:.1f}s): {pose_counts[-1] if pose_counts else 0} pose"""
        
        # Birkaç temsili frame'den detay ekle (başlangıç, orta, son)
        sample_indices = [0, len(body_data)//4, len(body_data)//2, 3*len(body_data)//4, len(body_data)-1]
        sample_indices = sorted(set(i for i in sample_indices if 0 <= i < len(body_data)))
        
        summary += "\n\nTemsili zaman noktalarından detaylar:"
        for idx in sample_indices:
            entry = body_data[idx]
            t = entry.get('timestamp', 0)
            poses = entry.get('poses', [])
            summary += f"\n  [{t:.1f}s] {len(poses)} pose tespit edildi"
            if poses and isinstance(poses[0], dict):
                # İlk pose'dan anahtar bilgileri ekle
                first_pose = poses[0]
                if 'confidence' in first_pose:
                    summary += f" (güven: {first_pose['confidence']:.2f})"
        
        return summary

    def _create_prompt(self, analysis_data):
        """
        Prompt oluşturur. Token bütçesini aşarsa, veri kaybını minimize ederek
        kademeli olarak küçültür.
        
        Küçültme önceliği (en az hassas → en hassas):
        1. body_data raw JSON → örnekleme → istatistiksel özet
        2. emotion_data raw JSON → sadece özet metni
        3. text_analysis → kırpma (baş + son korunur)
        """
        # Token bütçesi: 900K token (1M limitin altında güvenli marj)
        TOKEN_BUDGET = 900_000
        
        # Analiz verilerini metin formatına dönüştür
        audio_data = analysis_data.get('audio_summary', {})
        
        # Text analysis için güvenli erişim
        text_analysis_data = analysis_data.get('text_analysis', {})
        if isinstance(text_analysis_data, dict):
            text_analysis = text_analysis_data.get('text', '')
        else:
            text_analysis = ''
        
        # Boş metin kontrolü
        if not text_analysis or text_analysis.strip() == '':
            text_analysis = "Metin Analizi: Transkripsiyon verisi bulunamadı veya konuşma tespit edilemedi."
        
        emotion_data = analysis_data.get('emotion_data', {}).get('emotions', {})
        body_data = analysis_data.get('body_data', {}).get('analysis', [])

        # Danışan adını al
        client_name = analysis_data.get('client_name', 'Tanımsız')
        
        # Finetuning verilerinden örnekler ekle
        training_examples = "\n".join([
            f"Problem: {item['Problem']}\nAçıklama: {item['Açıklama']}"
            for item in self.training_data  # Tüm örnekleri kullan
        ])
        
        # Ses analizi verilerini özetle
        audio_summary = ""
        if audio_data and isinstance(audio_data, dict) and len(audio_data) > 0:
            rms_stats = audio_data.get('rms_stats', {})
            spectral_features = audio_data.get('spectral_features', {})
            audio_quality = audio_data.get('audio_quality', {})
            pitch_variations = audio_data.get('pitch_variations', {})
            temporal_features = audio_data.get('temporal_features', {})
            
            audio_summary = f"""
Ses Analizi Sonuçları:
- Ses Yoğunluğu: Ortalama {rms_stats.get('mean', 0):.3f}, Dinamik Aralık {rms_stats.get('dynamic_range', 0):.3f}
- Konuşma Hızı: {audio_quality.get('speech_rate', 0):.1f} olay/saniye
- Sessizlik Oranı: %{audio_quality.get('silence_ratio', 0)*100:.1f}
- Duraklamalar: {temporal_features.get('pause_count', 0)} adet
- Ses Tonu: Ortalama {pitch_variations.get('mean_pitch', 0):.1f} Hz, Kararlılık {pitch_variations.get('pitch_stability', 0):.2f}
- Sinyal Kalitesi: SNR {audio_quality.get('signal_to_noise_ratio', 0):.1f} dB
- Oturum Süresi: {temporal_features.get('duration', 0):.1f} saniye
"""
        else:
            audio_summary = "Ses Analizi: Veri bulunamadı veya ses dosyası işlenemedi."
        
        # Duygu verilerini zaman bazlı özetle (özet metin her zaman hazırlanır)
        emotion_summary_text = ""
        if emotion_data and isinstance(emotion_data, dict) and len(emotion_data) > 0:
            try:
                emotion_values = {}
                for emotion, value in emotion_data.items():
                    if isinstance(value, str) and '%' in value:
                        emotion_values[emotion] = float(value.replace('%', ''))
                    elif isinstance(value, (int, float)):
                        emotion_values[emotion] = float(value)
                    else:
                        emotion_values[emotion] = 0.0
                
                sorted_emotions = sorted(emotion_values.items(), key=lambda x: x[1], reverse=True)
                emotion_summary_text = "Duygusal Analiz Sonuçları:\n"
                emotion_summary_text += "\n".join([f"- {emotion}: {value:.1f}%" for emotion, value in sorted_emotions])
            except Exception as e:
                print(f"⚠️ Emotion data parse hatası: {e}")
                emotion_summary_text = f"Duygusal Analiz: {', '.join([f'{k}: {v}' for k, v in emotion_data.items()])}"
        else:
            emotion_summary_text = "Duygusal Analiz: Veri bulunamadı veya yüz tespit edilemedi."
        
        # Beden dili özet metin (her zaman hazırlanır)
        body_summary_text = ""
        if body_data and isinstance(body_data, list) and len(body_data) > 0:
            body_summary_text = self._summarize_body_data(body_data)
        else:
            body_summary_text = "Beden Dili Analizi: Veri bulunamadı veya yüz/vücut tespit edilemedi."
        
        # --- Sabit prompt parçaları (değişmeyenler) ---
        prompt_template = """
        Sen bir psikolojik danışmanlık uzmanısın. Aşağıdaki problemler ve açıklamalarına göre bir psikolojik danışma oturumunun analiz sonuçlarını değerlendirerek kapsamlı bir rapor hazırlayacağız. Aşağıda problemler ve açıklamaları yer almaktadır. Bununla birlikte, ses analizi, metin analizi, duygusal analiz ve beden dili analizi de ayrıca verilmiştir. Bu analizleri değerlendirerek kapsamlı bir rapor hazırlaya.
        
        Problemler ve Açıklamaları:
        {training_examples}
        
        Danışan Adı: {client_name}
        
        SES ANALİZİ:
        {audio_summary}
        
        Konuşma Metni:
        {text_analysis}
        
        DUYGUSAL ANALİZ:
        {emotion_section}
        
        Beden Dili Analizi:
        {body_section}
        
        Lütfen aşağıdaki başlıklar altında profesyonel bir değerlendirme yap:
        1. Psikolojik danışma seansının genel özeti (seansta üzerinde durulan ana temalar, danışanın genel görünümü, seanstaki işbirlikçi tutumu, seansta uygulanan müdahaleler/teknikler vb.)
        2. Psikolojik danışma seansında danışanın öne çıkan öznel ifadeleri
        3. Danışanın duygu, düşünce ve davranışlarına ilişkin değerlendirmeler:
            a. Danışanın duygu durumuna ilişkin tespitler (danışanın sergilediği duygular ve yoğunluğu/derecesi)
            b. Danışanın düşünce içeriklerine ilişkin tespitler (pozitif-negatif düşünce içerikleri vb.)
            c. Danışanın davranışsal tepkilerine ilişkin tespitler (örn: danışanın ilgili seansta ifade ettiği davranışları, sorumluluklarını erteleme, kalabalık ortamlara girmeme, aşırı alkol/sigara tüketme, ders devamsızlığı yapma vb.)
            d. Danışanın fizyolojik tepkilerine ilişkin tespitler (terleme, titreme, yüz kızarması vb.)
        4. Seansta uygulanan müdahale/tekniklerin danışan üzerindeki etkisine ilişkin tespitler
        5. Takip eden seanslarda üzerinde çalışılabilecek durumlar/konular, uygulanabilecek müdahaleler/teknikler
        6. Danışanın risk durumuna ilişkin tespitler (kendine zarar verme, intihar, başkalarına zarar verme, madde kullanımı vb.)
        7. Danışanın sevk durumuna ilişkin değerlendirmeler (danışan tıbbi veya psikiyatrik bir sevke ihtiyaç duyuyor mu?)
        
        Her başlık için detaylı ve profesyonel açıklamalar yap, önemli noktaları vurgula ve danışana yönelik öneriler sun.
        """
        
        # --- Sabit kısımların token maliyetini hesapla ---
        fixed_parts_size = (
            len(prompt_template) + len(training_examples) + 
            len(client_name) + len(audio_summary)
        )
        fixed_tokens = self._estimate_tokens(str(fixed_parts_size))
        
        # --- Değişken verileri tam haliyle hazırla ---
        emotion_full = json.dumps(emotion_data, indent=2, ensure_ascii=False)
        body_full = json.dumps(body_data, indent=2, ensure_ascii=False) if body_data else ""
        
        # --- Token tahminleri ---
        text_tokens = self._estimate_tokens(text_analysis)
        emotion_full_tokens = self._estimate_tokens(emotion_full)
        body_full_tokens = self._estimate_tokens(body_full)
        emotion_summary_tokens = self._estimate_tokens(emotion_summary_text)
        body_summary_tokens = self._estimate_tokens(body_summary_text)
        template_tokens = self._estimate_tokens(prompt_template + training_examples + client_name + audio_summary)
        
        total_full_tokens = template_tokens + text_tokens + emotion_full_tokens + body_full_tokens
        
        print(f"📊 Token bütçesi analizi:")
        print(f"   Sabit kısımlar: ~{int(template_tokens):,} token")
        print(f"   Konuşma metni: ~{int(text_tokens):,} token")
        print(f"   Duygu verisi (tam): ~{int(emotion_full_tokens):,} token")
        print(f"   Beden dili (tam): ~{int(body_full_tokens):,} token")
        print(f"   TOPLAM (tam): ~{int(total_full_tokens):,} token")
        print(f"   BÜTÇE: {TOKEN_BUDGET:,} token")
        
        # --- Bütçe içindeyse hiçbir şeye dokunma ---
        if total_full_tokens <= TOKEN_BUDGET:
            print(f"   ✅ Bütçe dahilinde, tüm veriler tam gönderiliyor.")
            emotion_section = emotion_full
            body_section = body_full if body_full else body_summary_text
        else:
            print(f"   ⚠️ Bütçe aşılıyor ({int(total_full_tokens - TOKEN_BUDGET):,} token fazla), kademeli küçültme uygulanıyor...")
            
            # Kalan bütçe (sabit + metin hariç)
            remaining_for_data = TOKEN_BUDGET - template_tokens - text_tokens
            
            # --- ADIM 1: Body data'yı örnekleyerek küçült ---
            emotion_section = emotion_full  # Duygu verisine henüz dokunma
            body_section = body_full
            
            if body_data and len(body_data) > 0:
                # Önce 2x örnekleme dene
                for downsample_factor in [2, 4, 8, 16]:
                    sampled = self._downsample_body_data(body_data, downsample_factor)
                    body_section = json.dumps(sampled, indent=2, ensure_ascii=False)
                    current_total = template_tokens + text_tokens + self._estimate_tokens(emotion_section) + self._estimate_tokens(body_section)
                    if current_total <= TOKEN_BUDGET:
                        print(f"   📉 Beden dili: {len(body_data)} → {len(sampled)} frame (her {downsample_factor}. frame)")
                        break
                else:
                    # Örnekleme yetmedi, istatistiksel özete geç
                    body_section = body_summary_text
                    print(f"   📉 Beden dili: Raw JSON → istatistiksel özet ({len(body_summary_text)} karakter)")
            
            # --- ADIM 2: Hâlâ aşıyorsa duygu verisini özetle ---
            current_total = template_tokens + text_tokens + self._estimate_tokens(emotion_section) + self._estimate_tokens(body_section)
            if current_total > TOKEN_BUDGET:
                emotion_section = emotion_summary_text
                print(f"   📉 Duygu verisi: Raw JSON → özet metin ({len(emotion_summary_text)} karakter)")
            
            # --- ADIM 3: Son çare — konuşma metnini kırp (baş + son korunur) ---
            current_total = template_tokens + self._estimate_tokens(text_analysis) + self._estimate_tokens(emotion_section) + self._estimate_tokens(body_section)
            if current_total > TOKEN_BUDGET:
                available_for_text = TOKEN_BUDGET - template_tokens - self._estimate_tokens(emotion_section) - self._estimate_tokens(body_section)
                available_chars = int(available_for_text * 3.5)  # Token → karakter
                
                if available_chars > 0 and len(text_analysis) > available_chars:
                    # Baş ve son eşit bölünür, ortaya "[...kırpıldı...]" eklenir
                    half = available_chars // 2 - 100  # Kırpma notu için yer bırak
                    original_len = len(text_analysis)
                    text_analysis = (
                        text_analysis[:half] +
                        f"\n\n[... Konuşma metninin ortasından {original_len - available_chars:,} karakter kırpıldı. "
                        f"Toplam orijinal uzunluk: {original_len:,} karakter ...]\n\n" +
                        text_analysis[-half:]
                    )
                    print(f"   📉 Konuşma metni: {original_len:,} → {len(text_analysis):,} karakter (baş+son korundu)")
            
            final_total = template_tokens + self._estimate_tokens(text_analysis) + self._estimate_tokens(emotion_section) + self._estimate_tokens(body_section)
            print(f"   📊 Küçültme sonrası toplam: ~{int(final_total):,} token")
        
        # --- Prompt'u oluştur ---
        prompt = prompt_template.format(
            training_examples=training_examples,
            client_name=client_name,
            audio_summary=audio_summary,
            text_analysis=text_analysis,
            emotion_section=emotion_section,
            body_section=body_section
        )
        
        return prompt
    
    def analyze_progress(self, client_name, session_analyses, date_range):
        """
        İlerleyiş analizi yapar - birden fazla oturum analizini karşılaştırır
        """
        try:
            print(f"\n=== İLERLEYİŞ ANALİZİ BAŞLADI ===")
            print(f"Danışan: {client_name}")
            print(f"Tarih Aralığı: {date_range}")
            print(f"Analiz Edilen Oturum Sayısı: {len(session_analyses)}")
            
            prompt = self._create_progress_prompt(client_name, session_analyses, date_range)
            print(f"İlerleyiş prompt hazırlandı, uzunluk: {len(prompt)} karakter")
            
            full_response, error = self._generate_with_continuation(prompt, temperature=0.8)

            if error:
                print(f"İlerleyiş analizi yanıt hatası: {error}")
                return {'analysis': f'İlerleyiş analizi yapılamadı. {error}', 'status': 'error'}

            result = {
                'analysis': full_response,
                'status': 'success',
                'sessions_count': len(session_analyses)
            }
            print(f"✅ İlerleyiş analizi başarılı (uzunluk: {len(full_response)} karakter)")
            return result
                
        except Exception as e:
            print(f"İlerleyiş analizi hatası: {str(e)}")
            return {
                'analysis': f'İlerleyiş analizi sırasında hata oluştu: {str(e)}',
                'status': 'error'
            }
    
    def _create_progress_prompt(self, client_name, session_analyses, date_range):
        """
        İlerleyiş analizi için özel prompt oluşturur
        """
        
        # Oturum analizlerini kronolojik sıraya koy
        sorted_analyses = sorted(session_analyses, key=lambda x: x['date'])
        
        # Her oturum için özet bilgi hazırla
        session_summaries = []
        for i, analysis in enumerate(sorted_analyses, 1):
            session_date = analysis['date'].strftime('%d.%m.%Y')
            session_title = analysis['title']
            
            # AI analizi varsa kullan, yoksa oturum notlarını kullan
            analysis_text = ""
            if analysis.get('ai_analysis'):
                analysis_text = analysis['ai_analysis']
            elif analysis.get('analysis_results'):
                analysis_text = analysis['analysis_results']
            elif analysis.get('notes'):
                analysis_text = f"Oturum Notları: {analysis['notes']}"
            else:
                analysis_text = "Bu oturum için detaylı analiz bulunmuyor."
            
            session_summary = f"""
OTURUM {i} - {session_title}
Tarih: {session_date}
Analiz:
{analysis_text}
{'='*60}
"""
            session_summaries.append(session_summary)
        
        # Training verilerinden örnekler
        training_examples = "\n".join([
            f"Problem: {item['Problem']}\nAçıklama: {item['Açıklama']}"
            for item in self.training_data[:5]  # İlk 5 örneği kullan
        ])
        
        prompt = f"""
Sen uzman bir psikolojik danışmanlık uzmanısın. Aşağıda bir danışanın {date_range} tarihleri arasındaki {len(session_analyses)} oturumunun analizi bulunmaktadır.

Bu oturum analizlerini kronolojik olarak inceleyerek danışanın psikolojik durumundaki değişimleri, ilerlemeleri ve gerilemeları analiz etmen gerekiyor.

REFERANS PROBLEM TİPLERİ:
{training_examples}

DANIŞAN: {client_name}
TARİH ARAĞI: {date_range}
TOPLAM OTURUM SAYISI: {len(session_analyses)}

OTURUM ANALİZLERİ:
{"".join(session_summaries)}

Lütfen aşağıdaki başlıklar altında kapsamlı bir ilerleyiş değerlendirmesi yap:

## 1. GENEL İLERLEYİŞ ÖZETİ
- Bu süreçte danışanın genel durumundaki değişim nedir?
- Olumlu gelişmeler nelerdir?
- Endişe verici durumlar var mı?

## 2. KRONOLOJIK DEĞİŞİM ANALİZİ
- İlk oturumdan son oturuma kadar hangi değişimler gözlemlendi?
- Hangi oturumlarda önemli dönüm noktaları yaşandı?
- Hangi dönemlerde gerileme gözlemlendi?

## 3. DUYGUSAL GELİŞİM
- Danışanın duygusal durumundaki değişimler
- Duygusal düzenleme becerilerindeki gelişim
- Stres yönetimi konusundaki ilerlemeler

## 4. DAVRANIŞSAL DEĞİŞİMLER
- Davranış kalıplarındaki değişiklikler
- Problem çözme becerilerindeki gelişim
- Sosyal ilişkilerdeki değişimler

## 5. BİLİŞSEL GELİŞİM
- Düşünce yapısındaki değişimler
- Kendini algılamasındaki gelişim
- Farkındalık düzeyindeki artışlar

## 6. ÖNERİLER VE GELECEK PLANLAMASI
- Mevcut ilerlemelerin sürdürülmesi için öneriler
- Dikkat edilmesi gereken konular
- Gelecek oturumlar için öneriler
- Danışma sürecinin devamına yönelik değerlendirme

Her başlık altında spesifik örnekler vererek, oturum tarihlerine referans yaparak detaylı açıklamalar yap.
Profesyonel, objektif ve danışan odaklı bir yaklaşım benimse.
"""
        
        return prompt 