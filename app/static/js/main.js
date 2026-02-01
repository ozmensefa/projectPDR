document.addEventListener('DOMContentLoaded', function() {
    // Video analiz sayfası kontrolü - gerekli elementler yoksa çıkış yap
    const videoUpload = document.getElementById('videoUpload');
    if (!videoUpload) {
        return; // Bu sayfa video analiz sayfası değil, script'i çalıştırma
    }
    
    const preview = document.getElementById('preview');
    const uploadLabel = document.querySelector('.upload-box label');
    const analyzeBtns = document.querySelectorAll('.analyze-btn');
    const resultDivs = document.querySelectorAll('.result');
    let selectedVideo = null;

    // Dosya yükleme işlemi
    videoUpload.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file && file.type.startsWith('video/')) {
            selectedVideo = file;
            displayVideoPreview(file);
            // Video yüklendiğinde buton metnini güncelle
            uploadLabel.textContent = "📁 Video'yu Değiştir";
        } else {
            alert('Lütfen geçerli bir video dosyası seçin');
            // Hatalı dosya seçiminde buton metnini sıfırla
            uploadLabel.textContent = "📁 Video Seç";
            preview.innerHTML = '';
            selectedVideo = null;
        }
    });

    // Video önizleme
    function displayVideoPreview(file) {
        const video = document.createElement('video');
        video.controls = true;
        video.src = URL.createObjectURL(file);
        preview.innerHTML = '';
        preview.appendChild(video);
    }

    // Ses analizi butonu için event listener
    document.querySelector('.analyze-audio-btn').addEventListener('click', async function() {
        if (!selectedVideo) {
            alert('Lütfen önce bir video yükleyin');
            return;
        }

        const resultDiv = document.querySelector('.audio-analysis-result');
        showLoading(resultDiv);

        const formData = new FormData();
        formData.append('video', selectedVideo);

        try {
            const response = await fetch('/analyze_audio', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                },
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            // Modal HTML'i
            const modalHtml = `
                <div id="imageModal" class="modal">
                    <span class="modal-close">&times;</span>
                    <img class="modal-content" id="modalImage">
                </div>
            `;

            // İki ayrı grafik ve modal göster
            resultDiv.innerHTML = `
                ${modalHtml}
                <div class="audio-plot">
                    <h4>Ses Seviyesi Analizi</h4>
                    <img src="data:image/png;base64,${data.plot_rms}" alt="Ses Seviyesi Grafiği" style="width:100%" class="zoomable-image">
                    <button class="download-btn download-plot-btn" data-plot="rms">Ses Seviyesi Grafiğini İndir</button>
                </div>
                <div class="audio-plot" style="margin-top: 20px;">
                    <h4>Dalga Formu Analizi</h4>
                    <img src="data:image/png;base64,${data.plot_wave}" alt="Dalga Formu Grafiği" style="width:100%" class="zoomable-image">
                    <button class="download-btn download-plot-btn" data-plot="wave">Dalga Formu Grafiğini İndir</button>
                </div>
            `;

            // Modal işlevselliği
            const modal = document.getElementById('imageModal');
            const modalImg = document.getElementById('modalImage');
            const closeBtn = document.querySelector('.modal-close');

            // Tüm zoomlanabilir görseller için tıklama olayı
            resultDiv.querySelectorAll('.zoomable-image').forEach(img => {
                img.addEventListener('click', function() {
                    modal.style.display = "block";
                    modalImg.src = this.src;
                });
            });

            // Modal kapatma butonu
            closeBtn.addEventListener('click', function() {
                modal.style.display = "none";
            });

            // Modal dışına tıklandığında kapatma
            modal.addEventListener('click', function(event) {
                if (event.target === modal) {
                    modal.style.display = "none";
                }
            });

            // ESC tuşu ile kapatma
            document.addEventListener('keydown', function(event) {
                if (event.key === "Escape" && modal.style.display === "block") {
                    modal.style.display = "none";
                }
            });

            // İndirme butonları için event listener'lar
            resultDiv.querySelectorAll('.download-plot-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const plotType = btn.getAttribute('data-plot');
                    const img = btn.previousElementSibling;
                    const link = document.createElement('a');
                    link.download = plotType === 'rms' ? 'ses_seviyesi.png' : 'dalga_formu.png';
                    link.href = img.src;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                });
            });

        } catch (error) {
            showError(resultDiv, `İşlem sırasında bir hata oluştu: ${error.message}`);
        }
    });

    // Metin analizi butonu için event listener
    document.querySelector('.analyze-text-btn').addEventListener('click', async function() {
        if (!selectedVideo) {
            alert('Lütfen önce bir video yükleyin');
            return;
        }

        const resultDiv = document.querySelector('.text-analysis-result');
        const downloadBtn = document.querySelector('.download-text-btn');
        resultDiv.textContent = 'Metin analizi yapılıyor...';
        downloadBtn.style.display = 'none';

        const formData = new FormData();
        formData.append('video', selectedVideo);

        try {
            const response = await fetch('/analyze_text', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            
            resultDiv.textContent = 'Analiz tamamlandı!';
            downloadBtn.style.display = 'block';
            
            downloadBtn.onclick = function() {
                const a = document.createElement('a');
                a.href = url;
                a.download = 'analiz_sonucu.txt';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            };

        } catch (error) {
            showError(resultDiv, `İşlem sırasında bir hata oluştu: ${error.message}`);
            downloadBtn.style.display = 'none';
        }
    });

    // Duygu analizi butonu için event listener
    document.querySelector('.analyze-emotion-btn').addEventListener('click', async function() {
        if (!selectedVideo) {
            alert('Lütfen önce bir video yükleyin');
            return;
        }

        const resultDiv = document.querySelector('.emotion-analysis-result');
        resultDiv.textContent = 'Duygu analizi yapılıyor...';

        const formData = new FormData();
        formData.append('video', selectedVideo);

        try {
            const response = await fetch('/analyze_emotion', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                },
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            // Modal HTML'i
            const modalHtml = `
                <div id="emotionImageModal" class="modal">
                    <span class="modal-close">&times;</span>
                    <img class="modal-content" id="emotionModalImage">
                </div>
            `;

            // Sonuçları göster
            resultDiv.innerHTML = `
                ${modalHtml}
                <img src="data:image/png;base64,${data.plot}" alt="Duygu Analizi Grafiği" style="width:100%" class="zoomable-image">
                <div class="analysis-details">
                    <h3>Duygu Analizi Sonuçları:</h3>
                    <p><strong>Baskın Duygu:</strong> ${data.dominant_emotion.emotion} (${data.dominant_emotion.intensity})</p>
                    <h4>Ortalama Duygu Yoğunlukları:</h4>
                    <ul>
                        ${Object.entries(data.emotions)
                            .map(([emotion, intensity]) => 
                                `<li>${emotion.charAt(0).toUpperCase() + emotion.slice(1)}: ${intensity}</li>`
                            ).join('')}
                    </ul>
                </div>
                <button class="download-btn download-plot-btn">Grafiği İndir</button>
            `;

            // Modal işlevselliği
            const modal = document.getElementById('emotionImageModal');
            const modalImg = document.getElementById('emotionModalImage');
            const closeBtn = modal.querySelector('.modal-close');
            const zoomableImage = resultDiv.querySelector('.zoomable-image');

            // Görsel tıklama olayı
            zoomableImage.addEventListener('click', function() {
                modal.style.display = "block";
                modalImg.src = this.src;
            });

            // Modal kapatma butonu
            closeBtn.addEventListener('click', function() {
                modal.style.display = "none";
            });

            // Modal dışına tıklandığında kapatma
            modal.addEventListener('click', function(event) {
                if (event.target === modal) {
                    modal.style.display = "none";
                }
            });

            // ESC tuşu ile kapatma
            document.addEventListener('keydown', function(event) {
                if (event.key === "Escape" && modal.style.display === "block") {
                    modal.style.display = "none";
                }
            });

            // Grafik indirme butonu için event listener
            const downloadPlotBtn = resultDiv.querySelector('.download-plot-btn');
            downloadPlotBtn.addEventListener('click', () => {
                const img = resultDiv.querySelector('img');
                const link = document.createElement('a');
                link.download = 'duygu_analizi_grafigi.png';
                link.href = img.src;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            });

        } catch (error) {
            showError(resultDiv, `İşlem sırasında bir hata oluştu: ${error.message}`);
        }
    });

    // Yapay Zeka analizi butonu için event listener
    document.querySelector('.analyze-ai-btn').addEventListener('click', async function() {
        if (!selectedVideo) {
            alert('Lütfen önce bir video yükleyin');
            return;
        }

        const resultDiv = document.querySelector('.ai-analysis-result');
        const downloadBtn = document.querySelector('.download-ai-btn');
        showLoading(resultDiv);
        downloadBtn.style.display = 'none';

        const formData = new FormData();
        formData.append('video', selectedVideo);

        try {
            const response = await fetch('/analyze_ai', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log("AI analiz sonuçları:", data); // Debug için

            if (data.error) {
                throw new Error(data.error);
            }

            // Analiz sonuçlarını göster
            if (data.analysis) {
                displayAIAnalysis(data);
                downloadBtn.style.display = 'block';
            } else {
                throw new Error('Analiz sonuçları bulunamadı');
            }

        } catch (error) {
            console.error("AI analiz hatası:", error); // Debug için
            showError(resultDiv, `İşlem sırasında bir hata oluştu: ${error.message}`);
            downloadBtn.style.display = 'none';
        }
    });

    // Beden dili analizi butonu için event listener
    document.querySelector('.analyze-body-language-btn').addEventListener('click', async function() {
        if (!selectedVideo) {
            alert('Lütfen önce bir video yükleyin');
            return;
        }

        const resultDiv = document.querySelector('.body-language-analysis-result');
        showLoading(resultDiv);

        const formData = new FormData();
        formData.append('video', selectedVideo);

        try {
            const response = await fetch('/analyze_body_language', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                },
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            // Modal HTML'i
            const modalHtml = `
                <div id="bodyLanguageModal" class="modal">
                    <span class="modal-close">&times;</span>
                    <img class="modal-content" id="bodyLanguageModalImage">
                </div>
            `;

            // Sonuçları göster
            resultDiv.innerHTML = `
                ${modalHtml}
                <div class="body-language-plot">
                    <h4>Beden Dili Analiz Grafiği</h4>
                    <img src="data:image/png;base64,${data.plot}" alt="Beden Dili Analizi Grafiği" class="zoomable-image" style="width:100%">
                    <button class="download-btn download-plot-btn">Grafiği İndir</button>
                </div>
                <div class="analysis-details" style="margin-top: 20px;">
                    <h4>Zaman Bazlı Analiz:</h4>
                    <ul>
                        ${data.analysis.map(item => `
                            <li>
                                <strong>${item.timestamp} sn:</strong> 
                                ${item.poses.map(p => `${p.pose} (${p.confidence}% güven)`).join(', ')}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;

            // Modal işlevselliği
            const modal = document.getElementById('bodyLanguageModal');
            const modalImg = document.getElementById('bodyLanguageModalImage');
            const closeBtn = modal.querySelector('.modal-close');
            const zoomableImage = resultDiv.querySelector('.zoomable-image');

            // Görsel tıklama olayı
            zoomableImage.addEventListener('click', function() {
                modal.style.display = "block";
                modalImg.src = this.src;
            });

            // Modal kapatma butonu
            closeBtn.addEventListener('click', function() {
                modal.style.display = "none";
            });

            // Modal dışına tıklandığında kapatma
            modal.addEventListener('click', function(event) {
                if (event.target === modal) {
                    modal.style.display = "none";
                }
            });

            // ESC tuşu ile kapatma
            document.addEventListener('keydown', function(event) {
                if (event.key === "Escape" && modal.style.display === "block") {
                    modal.style.display = "none";
                }
            });

            // Grafik indirme butonu için event listener
            const downloadPlotBtn = resultDiv.querySelector('.download-plot-btn');
            downloadPlotBtn.addEventListener('click', () => {
                const img = resultDiv.querySelector('.zoomable-image');
                const link = document.createElement('a');
                link.download = 'beden_dili_analizi.png';
                link.href = img.src;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            });

        } catch (error) {
            showError(resultDiv, `İşlem sırasında bir hata oluştu: ${error.message}`);
        }
    });

    function showError(resultDiv, message) {
        resultDiv.innerHTML = `
            <div class="error-message">
                <i class="error-icon">⚠️</i>
                <p>${message}</p>
            </div>
        `;
    }

    function showLoading(resultDiv) {
        resultDiv.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>İşleniyor...</p>
            </div>
        `;
    }

    // AI analizi sonuçlarını göster
    function displayAIAnalysis(data) {
        const resultDiv = document.querySelector('.ai-analysis-result');
        if (!resultDiv) {
            console.error("AI analysis result div not found.");
            return;
        }

        try {
            // Debug için ham veriyi görelim
            console.log("Gemini'den gelen veri:", data.analysis);

            // Markdown formatını HTML'e çevir
            let formattedContent = data.analysis
                // ### ile başlayan başlıkları <h2> yap
                .replace(/###\s+(.*?)(?=\n|$)/g, '<h2 style="color: #2c3e50; margin: 20px 0 10px 0; font-size: 1.5em;">$1</h2>')
                // ## ile başlayan başlıkları <h4> yap
                .replace(/##\s+(.*?)(?=\n|$)/g, '<h4 style="color: #34495e; margin: 25px 0 15px 0; font-size: 1.3em; border-bottom: 2px solid #3498db; padding-bottom: 8px;">$1</h4>')
                // Madde işaretlerini formatlı liste öğelerine dönüştür
                .replace(/\*\s+(.*?)(?=\n|$)/g, '<li style="margin: 8px 0;">$1</li>')
                // Kalın metinleri formatla
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

            // Liste öğelerini <ul> içine al
            formattedContent = formattedContent.replace(
                /(<li.*?>.*?<\/li>\n?)+/g,
                match => `<ul style="list-style-type: disc; margin: 10px 0 10px 20px;">${match}</ul>`
            );

            // Boş satırları paragraflara dönüştür
            formattedContent = formattedContent.replace(
                /(?:\r?\n){2,}/g,
                '</p><p style="margin: 10px 0; line-height: 1.6;">'
            );

            let htmlContent = `
                <div style="padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <p style="margin: 10px 0; line-height: 1.6;">
                        ${formattedContent}
                    </p>
                </div>
            `;

            resultDiv.innerHTML = htmlContent;

        } catch (error) {
            console.error('AI analizi görüntüleme hatası:', error);
            resultDiv.innerHTML = `<div class="error-message">Sonuçlar görüntülenirken bir hata oluştu: ${error.message}</div>`;
        }
    }

    // AI analizi için indirme butonu işlevselliği ekleyelim
    document.querySelector('.download-ai-btn').addEventListener('click', function() {
        const resultDiv = document.querySelector('.ai-analysis-result');
        const content = resultDiv.innerText;
        
        const blob = new Blob([content], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'ai_analiz_sonucu.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    });
}); 