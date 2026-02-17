# -*- coding: utf-8 -*-
import cv2
import mediapipe as mp
import matplotlib
matplotlib.use('Agg')  # Thread-safe, GUI gerektirmeyen backend
import matplotlib.pyplot as plt
import numpy as np
import io
import base64

class BodyLanguageService:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        
    def analyze(self, video_path):
        try:
            with self.mp_pose.Pose(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5) as pose:
                
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
                
                frame_interval = max(1, int(fps / 2))  # Yarım saniyede bir frame analiz et
                frame_count = 0
                analysis_results = []
                consecutive_errors = 0
                max_consecutive_errors = 10

                print(f"Vücut dili analizi başlıyor - FPS: {fps}, Toplam Frame: {total_frames}")

                while cap.isOpened():
                    try:
                        ret, frame = cap.read()
                        if not ret:
                            print(f"Video okuma tamamlandı (Frame: {frame_count})")
                            break
                        
                        # Frame geçerliliğini kontrol et
                        if frame is None or frame.size == 0:
                            print(f"⚠️ Geçersiz frame atlanıyor: {frame_count}")
                            frame_count += 1
                            consecutive_errors += 1
                            if consecutive_errors > max_consecutive_errors:
                                print(f"❌ Çok fazla ardışık hata, analiz durduruluyor")
                                break
                            continue
                        
                        # Başarılı frame okundu
                        consecutive_errors = 0

                        if frame_count % frame_interval == 0:
                            try:
                                # Frame'i RGB'ye çevir
                                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                results = pose.process(image)

                                if results.pose_landmarks:
                                    # Duruş analizi yap
                                    poses = self._determine_dominant_poses(results.pose_landmarks.landmark)
                                    
                                    timestamp = frame_count / fps
                                    analysis_results.append({
                                        "timestamp": round(timestamp, 1),
                                        "poses": poses
                                    })
                                    
                                    # İlerleme raporu
                                    if len(analysis_results) % 10 == 0:
                                        progress = (frame_count / total_frames) * 100
                                        print(f"Vücut dili analizi: {progress:.1f}% | {len(analysis_results)} pose tespit edildi")
                                        
                            except Exception as e:
                                print(f"⚠️ Frame {frame_count} pose analiz hatası: {str(e)}")

                        frame_count += 1
                        
                        # Güvenlik kontrolü
                        if frame_count > total_frames + 100:
                            print(f"⚠️ Frame sayısı beklenenin üzerinde, analiz sonlandırılıyor")
                            break
                            
                    except Exception as e:
                        print(f"❌ Video okuma hatası (Frame {frame_count}): {str(e)}")
                        consecutive_errors += 1
                        frame_count += 1
                        
                        if consecutive_errors > max_consecutive_errors:
                            print(f"❌ Çok fazla video okuma hatası, analiz durduruluyor")
                            break

                cap.release()

                if not analysis_results:
                    return {'error': 'Analiz sonuçları bulunamadı'}

                # Grafik oluştur ve sonuçları hazırla
                plot_data = self._create_analysis_plot(analysis_results)
                
                return {
                    'plot': plot_data,
                    'analysis': analysis_results
                }

        except Exception as e:
            raise Exception(f"Beden dili analizi hatası: {str(e)}")

    def _determine_dominant_poses(self, landmarks):
        """Vücut pozisyonunu analiz eder ve baskın duruşları belirler"""
        try:
            poses = []
            
            # Temel noktaları al
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
            left_elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW]
            right_elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW]
            left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST]
            right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST]
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]
            right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP]
            
            # Dik Duruş Analizi
            spine_angle = abs(
                np.arctan2(right_shoulder.y - right_hip.y, right_shoulder.x - right_hip.x) -
                np.arctan2(left_shoulder.y - left_hip.y, left_shoulder.x - left_hip.x)
            )
            if spine_angle < 0.2:
                poses.append({
                    "pose": "Dik Duruş",
                    "confidence": min(100, (1 - spine_angle / 0.2) * 100)
                })
                
            # Eller Önde Analizi
            hands_forward = (
                left_wrist.z < left_elbow.z and 
                right_wrist.z < right_elbow.z
            )
            if hands_forward:
                confidence = min(100, (
                    abs(left_wrist.z - left_elbow.z) + 
                    abs(right_wrist.z - right_elbow.z)
                ) * 200)
                poses.append({
                    "pose": "Eller Önde",
                    "confidence": confidence
                })
                
            # Diğer duruş analizleri...
            self._analyze_additional_poses(
                poses, landmarks,
                left_wrist, right_wrist,
                left_elbow, right_elbow,
                left_shoulder, right_shoulder,
                left_hip, right_hip
            )

            return poses

        except Exception as e:
            print(f"Poz belirleme hatası: {str(e)}")
            return []

    def _analyze_additional_poses(self, poses, landmarks,
                                left_wrist, right_wrist,
                                left_elbow, right_elbow,
                                left_shoulder, right_shoulder,
                                left_hip, right_hip):
        """Ek duruş analizlerini gerçekleştirir"""
        
        # Kollar Çapraz Analizi
        arms_crossed = (
            left_wrist.x > right_elbow.x and 
            right_wrist.x < left_elbow.x
        )
        if arms_crossed:
            confidence = min(100, (
                abs(left_wrist.x - right_elbow.x) + 
                abs(right_wrist.x - left_elbow.x)
            ) * 100)
            poses.append({
                "pose": "Kollar Çapraz",
                "confidence": confidence
            })
            
        # Eller Belde Analizi
        hands_on_hips = (
            abs(left_wrist.y - left_hip.y) < 0.1 and
            abs(right_wrist.y - right_hip.y) < 0.1
        )
        if hands_on_hips:
            confidence = min(100, (2 - (
                abs(left_wrist.y - left_hip.y) +
                abs(right_wrist.y - right_hip.y)
            )) * 100)
            poses.append({
                "pose": "Eller Belde",
                "confidence": confidence
            })
            
        # Eller Yukarıda Analizi
        hands_up = (
            left_wrist.y < left_shoulder.y and
            right_wrist.y < right_shoulder.y
        )
        if hands_up:
            confidence = min(100, (
                abs(left_shoulder.y - left_wrist.y) +
                abs(right_shoulder.y - right_wrist.y)
            ) * 100)
            poses.append({
                "pose": "Eller Yukarıda",
                "confidence": confidence
            })
            
        # Eller Yanda Analizi
        hands_side = (
            abs(left_wrist.x - left_shoulder.x) > 0.2 and
            abs(right_wrist.x - right_shoulder.x) > 0.2
        )
        if hands_side:
            confidence = min(100, (
                abs(left_wrist.x - left_shoulder.x) +
                abs(right_wrist.x - right_shoulder.x)
            ) * 100)
            poses.append({
                "pose": "Eller Yanda",
                "confidence": confidence
            })

    def _create_analysis_plot(self, analysis_results):
        """Analiz sonuçlarından grafik oluşturur"""
        plt.figure(figsize=(15, 8))
        
        # Her poz türü için ayrı çizgi
        pose_types = {'Dik Duruş', 'Eller Önde', 'Kollar Çapraz', 
                     'Eller Belde', 'Eller Yukarıda', 'Eller Yanda'}
        colors = {
            'Dik Duruş': 'green',
            'Eller Önde': 'blue',
            'Kollar Çapraz': 'red',
            'Eller Belde': 'purple',
            'Eller Yukarıda': 'orange',
            'Eller Yanda': 'brown'
        }
        
        for pose_type in pose_types:
            timestamps = []
            confidence_scores = []
            
            for result in analysis_results:
                timestamp = result["timestamp"]
                confidence = 0
                for pose in result["poses"]:
                    if pose["pose"] == pose_type:
                        confidence = pose["confidence"]
                        break
                
                timestamps.append(timestamp)
                confidence_scores.append(confidence)
            
            plt.plot(timestamps, confidence_scores, 
                    label=pose_type, 
                    color=colors[pose_type],
                    linewidth=2,
                    alpha=0.7)

        plt.title('Beden Dili Analizi - Poz Değişimleri', pad=20)
        plt.xlabel('Zaman (saniye)')
        plt.ylabel('Güven Skoru (%)')
        plt.grid(True, alpha=0.3)
        plt.legend(loc='upper right')
        plt.tight_layout()

        # Grafiği base64'e çevir
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png', bbox_inches='tight', dpi=300)
        img_buf.seek(0)
        plot_data = base64.b64encode(img_buf.getvalue()).decode()
        plt.close()

        return plot_data 