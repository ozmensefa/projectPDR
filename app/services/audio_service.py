# -*- coding: utf-8 -*-
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import io
import base64

class AudioService:
    def analyze(self, video_path, audio_path):
        try:
            y, sr = librosa.load(audio_path)
            
            # RMS Energy analizi
            rms_plot = self._create_rms_plot(y, sr)
            
            # Dalga formu analizi
            wave_plot = self._create_wave_plot(y, sr)
            
            # Detaylı ses analizi verileri
            audio_features = self._extract_audio_features(y, sr)
            
            return {
                'plot_rms': rms_plot,
                'plot_wave': wave_plot,
                'rms_stats': audio_features['rms_stats'],
                'spectral_features': audio_features['spectral_features'],
                'audio_quality': audio_features['audio_quality'],
                'pitch_variations': audio_features['pitch_variations'],
                'temporal_features': audio_features['temporal_features']
            }
            
        except Exception as e:
            raise Exception(f"Ses analizi hatası: {str(e)}")

    def _extract_audio_features(self, y, sr):
        """Detaylı ses özelliklerini çıkar"""
        
        # RMS istatistikleri
        rms = librosa.feature.rms(y=y)[0]
        rms_stats = {
            'mean': float(np.mean(rms)),
            'std': float(np.std(rms)),
            'min': float(np.min(rms)),
            'max': float(np.max(rms)),
            'dynamic_range': float(np.max(rms) - np.min(rms))
        }
        
        # Spektral özellikler
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
        
        spectral_features = {
            'spectral_centroid_mean': float(np.mean(spectral_centroids)),
            'spectral_rolloff_mean': float(np.mean(spectral_rolloff)),
            'zero_crossing_rate_mean': float(np.mean(zero_crossing_rate)),
            'spectral_centroid_std': float(np.std(spectral_centroids))
        }
        
        # Ses kalitesi göstergeleri
        audio_quality = {
            'signal_to_noise_ratio': self._calculate_snr(y),
            'silence_ratio': self._calculate_silence_ratio(rms),
            'speech_rate': self._estimate_speech_rate(y, sr)
        }
        
        # Pitch (ton) analizi
        try:
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            if pitch_values:
                pitch_variations = {
                    'mean_pitch': float(np.mean(pitch_values)),
                    'pitch_std': float(np.std(pitch_values)),
                    'pitch_range': float(np.max(pitch_values) - np.min(pitch_values)),
                    'pitch_stability': float(1.0 / (1.0 + np.std(pitch_values)))
                }
            else:
                pitch_variations = {
                    'mean_pitch': 0.0,
                    'pitch_std': 0.0,
                    'pitch_range': 0.0,
                    'pitch_stability': 0.0
                }
        except:
            pitch_variations = {
                'mean_pitch': 0.0,
                'pitch_std': 0.0,
                'pitch_range': 0.0,
                'pitch_stability': 0.0
            }
        
        # Zamansal özellikler
        temporal_features = {
            'duration': float(len(y) / sr),
            'tempo': float(librosa.beat.tempo(y=y, sr=sr)[0]),
            'energy_variance': float(np.var(rms)),
            'pause_count': self._count_pauses(rms)
        }
        
        return {
            'rms_stats': rms_stats,
            'spectral_features': spectral_features,
            'audio_quality': audio_quality,
            'pitch_variations': pitch_variations,
            'temporal_features': temporal_features
        }
    
    def _calculate_snr(self, y):
        """Sinyal-gürültü oranını hesapla"""
        try:
            signal_power = np.mean(y ** 2)
            noise_power = np.var(y - np.mean(y))
            if noise_power > 0:
                snr = 10 * np.log10(signal_power / noise_power)
                return float(snr)
            return float(20.0)  # Yüksek SNR varsayımı
        except:
            return float(10.0)
    
    def _calculate_silence_ratio(self, rms):
        """Sessizlik oranını hesapla"""
        try:
            threshold = np.mean(rms) * 0.1
            silence_frames = np.sum(rms < threshold)
            return float(silence_frames / len(rms))
        except:
            return float(0.1)
    
    def _estimate_speech_rate(self, y, sr):
        """Konuşma hızını tahmin et"""
        try:
            # Basit bir konuşma hızı tahmini
            onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
            duration = len(y) / sr
            if duration > 0:
                return float(len(onset_frames) / duration)
            return float(1.0)
        except:
            return float(1.0)
    
    def _count_pauses(self, rms):
        """Duraklamaları say"""
        try:
            threshold = np.mean(rms) * 0.1
            silent_frames = rms < threshold
            # Ardışık sessiz frame'leri grupla
            pause_count = 0
            in_pause = False
            for frame in silent_frames:
                if frame and not in_pause:
                    pause_count += 1
                    in_pause = True
                elif not frame:
                    in_pause = False
            return pause_count
        except:
            return 0

    def _create_rms_plot(self, y, sr):
        rms = librosa.feature.rms(y=y)[0]
        frame_time = np.linspace(0, len(y)/sr, len(rms))
        
        plt.figure(figsize=(15, 4))
        plt.plot(frame_time, rms, color='blue')
        plt.fill_between(frame_time, rms, alpha=0.5)
        plt.title('Ses Seviyesi (RMS Energy)')
        plt.xlabel('Zaman (s)')
        plt.ylabel('Genlik')
        plt.grid(True)
        plt.tight_layout()
        
        return self._fig_to_base64()

    def _create_wave_plot(self, y, sr):
        plt.figure(figsize=(15, 4))
        librosa.display.waveshow(y, sr=sr)
        plt.title('Dalga Formu')
        plt.xlabel('Zaman (s)')
        plt.ylabel('Genlik')
        plt.tight_layout()
        
        return self._fig_to_base64()

    def _fig_to_base64(self):
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode() 