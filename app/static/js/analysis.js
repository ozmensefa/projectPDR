document.addEventListener('DOMContentLoaded', function() {
    const videoForm = document.getElementById('video-form');
    const progressSection = document.getElementById('analysis-progress');
    const progressBar = progressSection.querySelector('.progress-bar');
    const progressText = document.getElementById('progress-text');
    const resultsSection = document.getElementById('analysis-results');
    const sessionId = new URLSearchParams(window.location.search).get('session_id');
    let analysisResults = {};

    videoForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        progressSection.style.display = 'block';
        videoForm.style.display = 'none';
        
        try {
            // Ses analizi
            updateProgress(20, 'Ses analizi yapılıyor...');
            const audioResult = await fetch('/analyze_audio', {
                method: 'POST',
                body: formData
            }).then(res => res.json());
            
            console.log('Ses analizi sonucu:', audioResult);  // Debug log
            document.getElementById('rms-plot').src = 'data:image/png;base64,' + audioResult.plot_rms;
            document.getElementById('wave-plot').src = 'data:image/png;base64,' + audioResult.plot_wave;
            analysisResults.audio = audioResult;

            // Metin analizi
            updateProgress(40, 'Konuşma analizi yapılıyor...');
            const textResult = await fetch('/analyze_text', {
                method: 'POST',
                body: formData
            }).then(res => res.json());
            
            console.log('Metin analizi sonucu:', textResult);  // Debug log
            document.getElementById('text-content').innerHTML = `<pre>${textResult.text}</pre>`;
            analysisResults.text = textResult;

            // Duygu analizi
            updateProgress(60, 'Duygu analizi yapılıyor...');
            const emotionResult = await fetch('/analyze_emotion', {
                method: 'POST',
                body: formData
            }).then(res => res.json());
            
            console.log('Duygu analizi sonucu:', emotionResult);  // Debug log
            document.getElementById('emotion-plot').src = 'data:image/png;base64,' + emotionResult.plot;
            document.getElementById('emotion-stats').innerHTML = formatEmotionStats(emotionResult);
            analysisResults.emotion = emotionResult;

            // Beden dili analizi
            updateProgress(80, 'Beden dili analizi yapılıyor...');
            const bodyResult = await fetch('/analyze_body_language', {
                method: 'POST',
                body: formData
            }).then(res => res.json());
            
            console.log('Beden dili analizi sonucu:', bodyResult);  // Debug log
            document.getElementById('body-plot').src = 'data:image/png;base64,' + bodyResult.plot;
            document.getElementById('body-stats').innerHTML = formatBodyStats(bodyResult);
            analysisResults.body = bodyResult;

            // AI analizi
            updateProgress(90, 'AI analizi yapılıyor...');
            await performAIAnalysis();

            updateProgress(100, 'Analiz tamamlandı!');
            progressBar.classList.add('bg-success');
            resultsSection.style.display = 'block';

            // AI sekmesine geç
            const aiTabLink = document.querySelector('a[href="#ai-tab"]');
            if (aiTabLink) {
                aiTabLink.click();
            }

        } catch (error) {
            console.error('Analiz hatası:', error);
            progressText.innerHTML = `Hata oluştu: ${error.message}`;
            progressBar.classList.add('bg-danger');
            showAlert('danger', 'Analiz sırasında bir hata oluştu: ' + error.message);
        }
    });

    if (document.getElementById('save-analysis')) {
        document.getElementById('save-analysis').addEventListener('click', async function() {
            try {
                const response = await fetch(`/save_analysis/${sessionId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(analysisResults)
                });
                
                if (response.ok) {
                    window.location.href = `/session/${sessionId}`;
                } else {
                    throw new Error('Kaydetme hatası');
                }
            } catch (error) {
                showAlert('danger', 'Analiz kaydedilirken bir hata oluştu: ' + error.message);
            }
        });
    }

    function updateProgress(percent, text) {
        progressBar.style.width = percent + '%';
        progressBar.setAttribute('aria-valuenow', percent);
        progressText.textContent = text;
    }

    function formatEmotionStats(result) {
        let html = '<ul class="list-group">';
        for (const [emotion, value] of Object.entries(result.emotions)) {
            html += `<li class="list-group-item d-flex justify-content-between align-items-center">
                ${emotion}
                <span class="badge bg-primary rounded-pill">${value}</span>
            </li>`;
        }
        html += '</ul>';
        return html;
    }

    function formatBodyStats(result) {
        let html = '<ul class="list-group">';
        for (const entry of result.analysis) {
            html += `<li class="list-group-item">
                <h6>Zaman: ${entry.timestamp}s</h6>
                <ul>`;
            for (const pose of entry.poses) {
                html += `<li>${pose.pose}: ${pose.confidence.toFixed(1)}%</li>`;
            }
            html += '</ul></li>';
        }
        html += '</ul>';
        return html;
    }

    // AI analizi yap ve sonuçları kaydet
    async function performAIAnalysis() {
        try {
            // Oturum bilgilerini al
            const sessionId = new URLSearchParams(window.location.search).get('session_id');
            const clientName = document.querySelector('h3.card-title')?.textContent.split('-')[1]?.trim() || 'Bilinmiyor';
            
            // AI analizi yap
            console.log("AI analizi başlıyor...");
            console.log("Gönderilecek veriler:", {
                session_id: sessionId,
                client_name: clientName,
                audio: analysisResults.audio,
                text: analysisResults.text,
                emotion: analysisResults.emotion,
                body: analysisResults.body
            });

            const response = await fetch('/analyze_ai', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    client_name: clientName,
                    audio: analysisResults.audio,
                    text: analysisResults.text,
                    emotion: analysisResults.emotion,
                    body: analysisResults.body
                })
            });

            // Yanıt kontrolü
            if (!response.ok) {
                let errorMessage = 'AI analizi sırasında bir hata oluştu';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {
                    errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }

            const aiResult = await response.json();
            console.log("AI analiz sonucu:", aiResult);

            // Hata kontrolü
            if (aiResult.status === 'error') {
                throw new Error(aiResult.analysis || 'AI analizi başarısız oldu');
            }

            // AI analizini göster
            const analysisContent = document.getElementById('analysis-content');
            const analysisInput = document.getElementById('analysis_text');
            
            if (analysisContent && analysisInput) {
                analysisContent.innerHTML = marked.parse(aiResult.analysis);
                analysisInput.value = aiResult.analysis;
            } else {
                console.error("AI analiz elementleri bulunamadı!");
            }

            // Analizi otomatik olarak kaydet
            if (sessionId) {
                try {
                    // AI analizini kaydet
                    const saveAIResponse = await fetch(`/save_ai_analysis/${sessionId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: `analysis_text=${encodeURIComponent(aiResult.analysis)}`
                    });
                    
                    if (saveAIResponse.ok) {
                        // Otomatik kaydetme mesajını göster
                        const autoSaveMessage = document.getElementById('auto-save-message');
                        if (autoSaveMessage) {
                            autoSaveMessage.style.display = 'block';
                            // 5 saniye sonra mesajı gizle
                            setTimeout(() => {
                                autoSaveMessage.style.display = 'none';
                            }, 5000);
                        }
                    } else {
                        console.error("AI analizi kaydedilemedi:", await saveAIResponse.text());
                    }
                } catch (saveError) {
                    console.error("AI analizi kaydedilirken hata:", saveError);
                }
                
                // Oturum analizini de kaydet
                const saveData = { ai: aiResult };
                console.log("Kaydedilecek veri:", saveData);

                const saveResponse = await fetch(`/save_analysis/${sessionId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(saveData)
                });

                const result = await saveResponse.json();
                console.log("Kaydetme sonucu:", result);

                if (result.success) {
                    showAlert('success', result.message);
                } else {
                    throw new Error(result.message || 'Kaydetme başarısız oldu');
                }
            }

            return true;

        } catch (error) {
            console.error("AI analiz hatası:", error);
            
            // Kullanıcı dostu hata mesajları
            let userMessage = error.message;
            if (error.message.includes('Failed to fetch')) {
                userMessage = 'Sunucuya bağlanılamadı. İnternet bağlantınızı kontrol edin ve tekrar deneyin.';
            } else if (error.message.includes('API yapılandırma hatası')) {
                userMessage = 'Sistem yapılandırma hatası. Lütfen sistem yöneticisiyle iletişime geçin.';
            } else if (error.message.includes('timeout')) {
                userMessage = 'İstek zaman aşımına uğradı. Lütfen tekrar deneyin.';
            }
            
            showAlert('danger', "AI analiz sırasında bir hata oluştu: " + userMessage);
            return false;
        }
    }



    // Yardımcı fonksiyonlar
    function showAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Container'ı bul
        const container = document.querySelector('.container');
        // İlk child elementi bul
        const firstChild = container.firstChild;
        // Alert'i container'ın en başına ekle
        container.insertBefore(alertDiv, firstChild);

        // 5 saniye sonra alert'i otomatik kaldır
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}); 