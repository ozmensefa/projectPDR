/**
 * YAKADES - Intro.js Etkileşimli Eğitim Rehberi (tour.js)
 * 
 * Bu dosya Yakades platformuna yeni katılan veya özellikleri hatırlamak isteyen
 * psikolojik danışmanlar için sayfa duyarlı rehber turlarını yönetir.
 */

(function () {
    'use strict';

    // Sayfa Seçicileri Yardımcı Fonksiyonu
    // Verilen listedeki ilk var olan CSS seçicisini döner, hiçbiri yoksa null döner.
    function getFirstExistingSelector(selectors) {
        for (const sel of selectors) {
            if (document.querySelector(sel)) {
                return sel;
            }
        }
        return null;
    }

    // Intro.js Türkçe Dil Desteği ve Premium Seçenekleri
    const introOptions = {
        nextLabel: 'İleri ›',
        prevLabel: '‹ Geri',
        skipLabel: 'Kapat',
        doneLabel: 'Tamamla',
        showBullets: true,
        showProgress: true,
        scrollToElement: true,
        scrollPadding: 30,
        overlayOpacity: 0.65,
        exitOnOverlayClick: false,
        exitOnEsc: true,
        keyboardNavigation: true
    };

    // Tüm Sayfalar İçin Eğitim Adımları Tanımları
    const tourSteps = {
        // 1. KONTROL PANELİ (DASHBOARD) TURU
        dashboard: [
            {
                title: 'YAKADES\'e Hoş Geldiniz!',
                intro: 'Kaygı bozukluklarına yönelik yapay zeka tabanlı Karar Destek Sistemini etkili şekilde kullanabilmeniz için hazırladığımız tura hoş geldiniz! Başlamak için <strong>İleri</strong> butonuna tıklayın.',
                position: 'center'
            },
            {
                element: '.navbar',
                title: 'Üst Menü ve Navigasyon',
                intro: 'Takviminize erişmek, danışan listesini görüntülemek ve platform genelinde kolayca gezinmek için bu üst menüyü kullanabilirsiniz.',
                position: 'bottom'
            },
            {
                element: '#dashboardClientsTable',
                fallbackSelectors: ['.card:has(table)', '.card:first-of-type'],
                title: 'Aktif Danışanlarınız',
                intro: 'Takibinizdeki aktif danışanları, son ve gelecek seans durumlarıyla birlikte buradan izleyebilirsiniz. Danışanın detaylarına gitmek veya yeni oturum eklemek için tablodaki aksiyon butonlarını kullanabilirsiniz.',
                position: 'top'
            },
            {
                element: '.upcoming-sessions-container',
                fallbackSelectors: ['.card:has(.fa-calendar-check)'],
                title: 'Yaklaşan Oturumlar',
                intro: 'Planlanan gelecek oturumlarınızı kronolojik sırada buradan takip edebilir, doğrudan oturum detaylarına gidip gerekli düzenlemeleri yapabilirsiniz.',
                position: 'top'
            },
            {
                element: '.recent-sessions-list',
                fallbackSelectors: ['.card:has(.fa-history)'],
                title: 'Geçmiş Oturumlar ve AI Durumları',
                intro: 'Tamamlanan son oturumları ve bunlara ait yapay zeka analiz süreçlerinin (İşleniyor, Tamamlandı, Bekliyor) durumunu buradan canlı olarak izleyebilirsiniz.',
                position: 'top'
            },
            {
                element: '#darkModeToggle',
                title: 'Karanlık / Aydınlık Mod',
                intro: 'Çalışma konforunuza göre ekran temasını dilediğiniz an buradan değiştirebilirsiniz. Gece veya loş ortamlarda karanlık tema gözlerinizi yormaz.',
                position: 'bottom'
            },
            {
                element: '#notificationDropdown',
                title: 'Akıllı Bildirimler',
                intro: 'Yapay zeka analiz raporları başarıyla hazırlandığında veya sistem güncellemelerinde anlık bilgilendirmeleri buradan alırsınız.',
                position: 'bottom'
            }
        ],

        // 2. DANIŞAN LİSTESİ (MY CLIENTS) TURU
        clientsList: [
            {
                element: '.page-header',
                title: 'Danışan Yönetimi',
                intro: 'Burası sisteminizde kayıtlı olan tüm danışanlarınızı merkezi olarak izleyip yönetebileceğiniz ana danışan sayfasıdır.',
                position: 'bottom'
            },
            {
                element: 'a[href*="/client/add"]',
                fallbackSelectors: ['.page-header a.btn-primary', '.btn-primary'],
                title: 'Yeni Danışan Kaydı',
                intro: 'Sisteme yeni bir danışan tanımlamak için bu butonu kullanın. Danışanın yaş, cinsiyet, iletişim ve öz geçmiş bilgilerini girerek hemen süreci başlatabilirsiniz.',
                position: 'left'
            },
            {
                element: '#clientsListTable_filter',
                fallbackSelectors: ['input[type="search"]', '#clientsListTable_filter input'],
                title: 'Hızlı Arama ve Arama Kutusu',
                intro: 'Danışan listeniz büyüdüğünde, isim veya diğer bilgilerle filtreleme yaparak aradığınız kişiye saniyeler içinde ulaşabilirsiniz.',
                position: 'bottom'
            },
            {
                element: '.btn-action-group',
                fallbackSelectors: ['#clientsListTable tbody tr:first-child .btn-action-group', 'table .btn-info'],
                title: 'İşlemler Menüsü',
                intro: 'Bu alandaki hızlı menülerle; danışanın detaylı profiline gidebilir, hızlı oturum kaydı oluşturabilir veya danışan kaydını silebilirsiniz.',
                position: 'left'
            }
        ],

        // 3. DANIŞAN PROFİLİ (CLIENT PROFILE) TURU
        clientProfile: [
            {
                element: '.img-thumbnail',
                fallbackSelectors: ['.card:first-of-type img'],
                title: 'Danışan Fotoğrafı',
                intro: 'Danışanınızın kişisel profil resmi ve sisteme ilk kayıt tarihi bu kartta görüntülenir.',
                position: 'right'
            },
            {
                element: '.col-md-4 .card:nth-of-type(2)',
                fallbackSelectors: ['.card:nth-of-type(2)'],
                title: 'Kişisel Bilgiler',
                intro: 'Danışanın yaşı, cinsiyeti, telefon veya e-posta gibi iletişim bilgileri ile şimdiye kadar tamamlanan seanslarının toplam sayısı burada listelenir.',
                position: 'right'
            },
            {
                element: '.page-header .btn-success',
                fallbackSelectors: ['a[href*="add_session"]', '.btn-success'],
                title: 'Yeni Oturum Ekle',
                intro: 'Danışanınızla gerçekleştireceğiniz yeni bir psikolojik danışmanlık oturumunu sisteme kaydetmek ve yapay zeka video analizini başlatmak için bu butonu kullanabilirsiniz.',
                position: 'bottom'
            },
            {
                element: '#sessionsTable',
                fallbackSelectors: ['.card:has(table)'],
                title: 'Oturum Geçmişi ve Rapor Durumu',
                intro: 'Danışanınızla gerçekleştirdiğiniz tüm oturumların listesi buradadır. Oturuma ait video yükleme ve yapay zeka analiz raporunun durumunu buradan görebilir, oturum detayına gidebilirsiniz.',
                position: 'top'
            },
            {
                element: 'a[href*="/progress_analysis/"]',
                fallbackSelectors: ['.btn-info'],
                title: 'İlerleyiş Analizi',
                intro: 'Danışanın birden çok oturumu arasındaki ruh hali, kaygı seviyeleri ve beden dili gelişimini karşılaştıran derinlemesine bir <strong>İlerleyiş Raporu</strong> başlatmak için bu butona tıklayabilirsiniz.',
                position: 'left'
            },
            {
                element: '.suggestions-container',
                fallbackSelectors: ['.card:has(.fa-lightbulb)'],
                title: 'Yapay Zeka Karar Önerileri',
                intro: 'YAKADES, danışanın son oturum analiz sonuçlarını inceleyerek sonraki seanslar için size özel otomatik süreç önerileri ve klinik tavsiyeler üretir. Karar süreçlerinizde size destek olur!',
                position: 'top'
            }
        ],

        // 4. OTURUM DETAYI (SESSION DETAIL) TURU
        sessionDetail: [
            {
                element: '.session-card-video',
                title: 'Video Yönetim Paneli',
                intro: 'Gerçekleştirdiğiniz oturuma ait video kaydını bu alana güvenli şekilde sürükleyip bırakarak yükleyebilirsiniz. Yüklenen video üzerinde AI analizi yapılacaktır.',
                position: 'top'
            },
            {
                element: 'button[onclick="startAsyncAnalysis()"]',
                fallbackSelectors: ['.alert-info button', '.alert-info .btn-primary'],
                title: 'Yapay Zeka Analizini Başlat',
                intro: 'Video yüklendikten sonra bu butona basarak analizi başlatırsınız. Analiz arka planda sürerken sayfayı güvenle kapatabilirsiniz. Süreç bittiğinde sistem sizi bildirimle uyaracaktır.',
                position: 'top'
            },
            {
                element: '.session-card-report',
                title: 'Yapay Zeka Oturum Raporu',
                intro: 'Analiz bittiğinde; danışanın saniye saniye duygu değişimleri, kaygı seviyesi göstergeleri, beden dili bulguları ve konuşma analizi bu alanda detaylı bir rapor halinde yayınlanır.',
                position: 'top'
            },
            {
                element: '.btn-group[aria-label="Font boyutu"]',
                fallbackSelectors: ['.btn-group-sm'],
                title: 'Metin Boyutu Ayarları',
                intro: 'Yapay zeka raporunu daha rahat okumak için font boyutunu büyütebilir, küçültebilir veya orijinal boyutuna sıfırlayabilirsiniz.',
                position: 'bottom'
            },
            {
                element: '#download-report',
                title: 'Raporu İndir ve Arşivle',
                intro: 'Üretilen bu kapsamlı yapay zeka analiz raporunu Word (.docx) veya Düz Metin (.txt) formatlarında bilgisayarınıza indirebilirsiniz.',
                position: 'top'
            },
            {
                element: '.notes-section',
                title: 'Danışman Özel Notları',
                intro: 'Oturum esnasında veya sonrasında aldığınız kişisel gözlem ve klinik notları buraya yazabilirsiniz. Bu alan tamamen şifreli olup, sadece sizin tarafınızdan görülebilir.',
                position: 'top'
            },
            {
                element: '#manual-save',
                title: 'Değişiklikleri Kaydet',
                intro: '<strong>Dikkat:</strong> Not alanına yazdığınız gözlemlerinizin kaybolmaması için mutlaka bu "Kaydet" butonuna basarak veritabanına kaydetmelisiniz.',
                position: 'top'
            },
            {
                element: '.techniques-section',
                title: 'Uygulanan Psikolojik Teknikler',
                intro: 'Bu seansta danışana uyguladığınız psikolojik teknikleri (örneğin BDT egzersizleri, Nefes Teknikleri) buraya yazın. Böylece yapay zeka bir sonraki gelişim raporunda bu tekniklerin etkinliğini ölçümleyecektir.',
                position: 'top'
            }
        ],

        // 5. YENİ İLERLEYİŞ ANALİZİ (GENERATE PROGRESS ANALYSIS) TURU
        generateAnalysis: [
            {
                element: '.alert-info',
                title: 'İlerleyiş Analizi Nedir?',
                intro: 'Danışanın kaygı seviyelerindeki düşüşü, beden dili gelişimini ve uyguladığınız psikolojik tekniklerin başarısını birden fazla seans genelinde karşılaştırmalı olarak ölçen akıllı bir rapordur.',
                position: 'bottom'
            },
            {
                element: '#start_session_id',
                title: 'Başlangıç Oturumu',
                intro: 'Karşılaştırmanın başlayacağı ilk (eski) oturumu buradan seçin.',
                position: 'bottom'
            },
            {
                element: '#end_session_id',
                title: 'Bitiş Oturumu',
                intro: 'Gelişimi kıyaslamak istediğiniz son (yeni) oturumu buradan seçin.',
                position: 'bottom'
            },
            {
                element: '#range-info',
                fallbackSelectors: ['#progress-form'],
                title: 'Analiz Süre ve Oturum Bilgisi',
                intro: 'Seçimleri tamamladığınızda, analiz edilecek toplam oturum sayısı ve yapay zekanın tahmini rapor üretme süresi burada otomatik hesaplanır.',
                position: 'top'
            },
            {
                element: '#generate-btn',
                title: 'İlerleyiş Analizi Oluştur',
                intro: 'Tüm seçimleriniz doğruysa, bu butona tıklayarak derin gelişim analizini arka planda başlatabilirsiniz. Rapor hazırlandığında bildirim alacaksınız.',
                position: 'top'
            }
        ],

        // 6. İLERLEYİŞ RAPORU GÖRÜNÜMÜ (VIEW PROGRESS REPORT) TURU
        viewReport: [
            {
                element: '.border-left-primary',
                fallbackSelectors: ['.card:has(.text-primary)'],
                title: 'Danışan Bilgileri',
                intro: 'Raporun üretildiği danışana ait temel demografik veriler ve yaş bilgisi burada özetlenir.',
                position: 'bottom'
            },
            {
                element: '.border-left-info',
                fallbackSelectors: ['.card:has(.text-info)'],
                title: 'Karşılaştırılan Seans Bilgileri',
                intro: 'Karşılaştırılan başlangıç ve bitiş seanslarının başlıkları ile bu seanslar arasında geçen toplam gün sayısını buradan görebilirsiniz.',
                position: 'bottom'
            },
            {
                element: '#main-report',
                fallbackSelectors: ['.session-card-report'],
                title: 'Karşılaştırmalı Gelişim Raporu',
                intro: 'Yapay zekanın çıkardığı detaylı seans karşılaştırma analizleri, kaygı skorlarındaki gerilemeler ve gelişim grafikleri burada listelenir.',
                position: 'top'
            },
            {
                element: 'button[data-bs-target="#downloadFormatModal"]',
                fallbackSelectors: ['.btn-success'],
                title: 'Raporu İndir',
                intro: 'Gelişim raporunu Word (.docx) veya Metin (.txt) formatlarında bilgisayarınıza indirebilirsiniz.',
                position: 'bottom'
            },
            {
                element: 'button[onclick="printReport()"]',
                fallbackSelectors: ['.btn-info'],
                title: 'Yazdır veya PDF Kaydet',
                intro: 'Raporu yazıcıya gönderebilir veya yazdırma penceresinde "PDF olarak kaydet" seçeneğini seçerek bilgisayarınıza PDF formatında kaydedebilirsiniz.',
                position: 'bottom'
            },
            {
                element: '.session-card-danger',
                fallbackSelectors: ['.card:has(.session-card-header-danger)'],
                title: 'Tehlikeli İşlemler Bölgesi',
                intro: 'Bu ilerleyiş raporunu kalıcı olarak silmek isterseniz bu alanı kullanabilirsiniz. Rapor silinse dahi seanslara ait orijinal verileriniz asla silinmez.',
                position: 'top'
            }
        ]
    };

    // Mevcut sayfa URL'sine göre doğru adımları tespit eden router fonksiyonu
    function getStepsForCurrentPage() {
        const path = window.location.pathname;

        // 1. Ana Sayfa (Dashboard)
        if (path === '/' || path === '/index') {
            return tourSteps.dashboard;
        }

        // 2. Danışan Listesi
        if (path === '/clients' || path === '/client/list') {
            return tourSteps.clientsList;
        }

        // 3. İlerleyiş Analizi Oluşturma Paneli
        if (path.indexOf('/progress_analysis/') !== -1) {
            return tourSteps.generateAnalysis;
        }

        // 4. İlerleyiş Raporu Sayfası
        if (path.indexOf('/progress_report/') !== -1 || path.indexOf('/view_progress_report/') !== -1) {
            return tourSteps.viewReport;
        }

        // 5. Oturum Detay Sayfası
        if (path.indexOf('/session/view/') !== -1 || (path.indexOf('/session/') !== -1 && path.indexOf('/edit') === -1 && path.indexOf('/delete') === -1)) {
            return tourSteps.sessionDetail;
        }

        // 6. Danışan Profil Sayfası (DİKKAT: Üsttekilerle çakışmaması için en son kontrol edilir)
        if (path.indexOf('/client/') !== -1 && path.indexOf('/add') === -1 && path.indexOf('/edit') === -1) {
            return tourSteps.clientProfile;
        }

        // Bulunamadı
        return null;
    }

    // Eğitim turunu başlatan ana fonksiyon
    function startYakadesTour() {
        const pageSteps = getStepsForCurrentPage();

        // Eğer bu sayfaya özel adımlar tanımlanmamışsa, şık bir yönlendirme pop-up'ı gösterelim
        if (!pageSteps) {
            const tempIntro = introJs();
            tempIntro.setOptions({
                ...introOptions,
                steps: [{
                    element: document.querySelector('#startTourBtn') || undefined,
                    title: 'Yardım ve Rehberlik',
                    intro: 'Şu an bulunduğunuz sayfaya özel bir eğitim rehberi bulunmamaktadır.<br><br>Yakades platformunun tüm ana özelliklerini öğrenmek için sizi <strong>Kontrol Paneline (Dashboard)</strong> yönlendirelim mi?',
                    position: 'bottom'
                }],
                nextLabel: 'Kontrol Paneline Git',
                doneLabel: 'Kontrol Paneline Git',
                showBullets: false,
                showProgress: false
            });

            tempIntro.oncomplete(function () {
                window.location.href = '/';
            });
            tempIntro.onexit(function () {
                // Sessizce kapat
            });

            tempIntro.start();
            return;
        }

        // DOM'da var olmayan elementlere sahip adımları temizleyelim (Robust Hata Yönetimi)
        const filteredSteps = [];

        for (const step of pageSteps) {
            if (!step.element) {
                // Floating step (örneğin hoş geldin mesajı) her zaman eklenir
                filteredSteps.push(step);
                continue;
            }

            // Birincil seçiciyi kontrol et
            let activeSelector = step.element;
            if (!document.querySelector(activeSelector)) {
                // Eğer birincil seçici yoksa yedekleri kontrol et
                if (step.fallbackSelectors) {
                    const foundFallback = getFirstExistingSelector(step.fallbackSelectors);
                    if (foundFallback) {
                        activeSelector = foundFallback;
                    } else {
                        // Yedekler de yoksa adımı atla
                        continue;
                    }
                } else {
                    // Yedek yoksa adımı atla
                    continue;
                }
            }

            // Adımı güncel ve var olan seçiciyle ekle
            filteredSteps.push({
                element: activeSelector,
                title: step.title,
                intro: step.intro,
                position: step.position || 'auto'
            });
        }

        // Eğer filtrelenmiş adımlar boş ise (olağanüstü boş durum)
        if (filteredSteps.length === 0) {
            alert('Rehber başlatılamadı: Bu sayfada hedeflenen hiçbir arayüz elementi bulunamadı.');
            return;
        }

        // Intro.js Başlatma
        const tourInstance = introJs();
        tourInstance.setOptions({
            ...introOptions,
            steps: filteredSteps
        });

        // Tur tamamlandığında şık bir tebrik mesajı veya loglama yapılabilir
        tourInstance.oncomplete(function () {
            // İsteğe bağlı olarak kullanıcının turu tamamladığı localStorage'da saklanabilir
            localStorage.setItem('yakades_tour_completed_' + window.location.pathname, 'true');
        });

        tourInstance.start();
    }

    // Sayfa yüklendiğinde ve Yardım butonu hazır olduğunda tetikleyiciyi bağlayalım
    document.addEventListener('DOMContentLoaded', function () {
        const startTourBtn = document.getElementById('startTourBtn');
        const tourNavContainer = document.getElementById('tourNavContainer');
        
        if (startTourBtn) {
            // Sadece eğitime sahip sayfalarda butonu göster
            const steps = getStepsForCurrentPage();
            if (steps && steps.length > 0) {
                if (tourNavContainer) {
                    tourNavContainer.style.setProperty('display', 'flex', 'important');
                }
            }

            startTourBtn.addEventListener('click', function (e) {
                e.preventDefault();
                startYakadesTour();
            });

            // Danışanın ilk girişi ise (otomatik başlatma isteğe bağlıdır, 
            // ancak rahatsız etmemek adına sadece butona tıklanınca başlaması tercih edilmiştir)
            // İsteğe bağlı otomatik tetikleme kodu aşağıya eklenebilir.
        }
    });

})();
