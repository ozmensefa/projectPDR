Yapılanlar
1. Raporlama Özelleştirmeleri:
Güncelleme tamamlandı. ai_service.py'deki prompt'a şu 3 kritik değişiklik yapıldı:
Yeni başlık eklendi → "Oturumların Sonlandırılması veya Gelecek Oturum İçin Önerilerin Verilmesi"
Teknik öneri detaylandırması → "BDT uygulayabilirsiniz" gibi genel ifadeler yerine, spesifik teknik adları, örnekleri ve uygulama yönergeleri istenecek. Ayrıca seansta zaten uygulanmış olan teknikler tespit edilerek bunlar tekrar "yeni öneri" olarak sunulmayacak.
Beden dili yorum koruyucusu → Rahat oturma, bacak bacak üstüne atma gibi davranışlar artık otomatik olarak "savunmacılık" veya "mesafe koyma" şeklinde olumsuz yorumlanmayacak. Beden dili bulguları ancak sözel ifadeler ve duygu analiziyle tutarlıysa anlamlı bulgu olarak raporlanacak.

2. "Uygulanan Teknikler" Özelliği Tamamlandı
Yapılan Değişiklikler (7 dosya):
Dosya	Değişiklik
models.py	Session modeline applied_techniques (Text) kolonu eklendi
forms.py	SessionForm'a applied_techniques textarea alanı eklendi
client.py	add_session ve edit_session route'larında yeni alan işleniyor
routes.py	/save_applied_techniques/<session_id> AJAX endpoint'i eklendi
tasks.py	combined_data'ya applied_techniques eklendi → AI'ya iletiliyor
ai_service.py	Prompt'a koşullu DANIŞMAN TARAFINDAN UYGULANAN TEKNİKLER bölümü eklendi
Templates	add_session.html, edit_session.html, view_session.html güncellendi
Veritabanı	session tablosuna applied_techniques kolonu migrate edildi
Nasıl Çalışıyor:
Danışman teknik girerse → Raporda "Uygulanan Teknikler" bölümü görünür, AI bu teknikleri yeni öneri olarak sunmaz
Danışman teknik girmezse → Bu bölüm raporda yer almaz, mevcut davranış korunur
Teknikler hem oturum ekleme/düzenleme formunda hem de oturum detay sayfasında girilebilir

3. Durum Bildirim Sistemi Güncellendi
Oturum listesindeki "Durum" sütunu artık 6 farklı durum gösteriyor:

Badge	Durum	Açıklama
🟡 bg-warning	Video Yüklenmedi	Henüz video yüklenmemiş oturumlar
🔵 bg-primary	Analiz Bekliyor	Video yüklenmiş ama analiz başlatılmamış
⚪ bg-secondary	Sırada Bekliyor	Analiz sıraya alınmış (queued)
🔵 bg-info + spinner	Analiz Ediliyor	Analiz aktif olarak işleniyor
🟢 bg-success	Analiz Tamamlandı	Analiz başarıyla bitti
🔴 bg-danger	Analiz Başarısız	Analiz hata verdi
⚫ bg-dark	Analiz İptal Edildi	Analiz iptal edildi

4. Logo tasarımları yapıldı. Landing page, login page, register page, index page ve base.html dosyalarındaki logolar güncellendi. Tarayıcı tab'ında çıkan logo da güncellendi.

5. faster-whisper large v3 modeli kuruldu ve varsayılan model olarak ayarlandı. Transkripsiyon işlemleri daha başarılı hale geldi.

6. Karanlık mod eklendi. Glassmorphism tasarımı yapıldı.

7. Mobil kullanımda tablolu içerikler sayfaya sığmıyor sorunu çözüldü.

8. Takvim sayfasındaki oturumlar kişiye göre renklendirildi.




Yapılacaklar
göze gelen birkaç ufak düzeltme var:
1. yakades logosu biraz daha büyük olabilir. tarayıcıda logonun height değerini 40px'ten 60'a yükselttim, güzel gözüktü. öyle ayarlayabiliriz.
2. yeni oturum ekleme sayfasındaki placeholder'lar yeni satıra geçmiş gözüküyor. bunu fixleyelim. karanlık modda oturum tarihi alanındaki sağ tarafta takvim seçme logosu siyah kalmış.
3. takvim sayfasındaki oturumlar kişiye göre renklendirilebilir. bir danışmanın birden fazla danışanı varsa onlara ait renkler farklı olabilir.
















Oluşturulan Oturum Analizi raporları aşağıdaki başlıkların her birini mutlaka içermeli:
1. Psikolojik danışma seansının genel özeti (seansta üzerinde durulan ana temalar, danışanın genel görünümü, seanstaki işbirlikçi tutumu, seansta uygulanan müdahaleler/teknikler vb.)
2. Psikolojik danışma seansında danışanın öne çıkan öznel ifadeleri
3. Danışanın duygu, düşünce ve davranışlarına ilişkin değerlendirmeler:
   a. Danışanın duygu durumuna ilişkin tespitler (danışanın sergilediği duygular ve yoğunluğu)
   b. Danışanın düşünce içeriklerine ilişkin tespitler (pozitif, negatif ve nötr düşünceler vb.)
   c. Danışanın davranışsal tepkilerine ilişkin tespitler (danışanın ilgili seansta ifade ettiği davranışları, sorumluluklarını erteleme, kalabalık ortamlara girmeme, ders devamsızlığı yapma vb.)
   d. Danışanın fizyolojik tepkilerine ilişkin tespitler (terleme, titreme, yüz kızarması vb.)
4. Seansta uygulanan müdahale/tekniklerin danışan üzerindeki etkisine ilişkin tespitler
5. Takip eden seanslarda üzerinde çalışılabilecek durumlar/konular, uygulanabilecek müdahaleler/teknikler
6. Danışanın risk durumuna ilişkin tespitler (kendine zarar verme, intihar, başkalarına zarar verme, madde kullanımı vb.)
7. Danışanın sevk durumuna ilişkin değerlendirmeler (danışan tıbbi veya psikiyatrik bir sevke ihtiyaç duyuyor mu?)
8. Oturumların Sonlandırılması veya Gelecek Oturum İçin Önerilerin Verilmesi

Raporlamanın sonunda ileriki oturumlar için önerilerin verildiği bölümde "BDT uygulayabilirsiniz" gibi genel ifadeler yerine, ilgili ekole bağlı hangi bilişsel tekniklerin uygulanabileceğinin detaylandırılması ve örneklendirilmesini yapalım. Seans içerisinde danışman tarafından zaten uygulanmış olan tekniklerin sistem tarafından saptanarak, bir sonraki seans için yeni bir "öneri" olarak sunulmasının önüne geçilmesi gerekiyor. Ayrıca beden dili analizlerinde danışanın rahat tavırlarının veya kişisel farklılıklarının sistem tarafından "olumsuza yorma" eğiliminin azaltılması gerekiyor.

Oturum içerisinde danışman tarafından uygulanan teknikler tespit edilmeli. Danışanlar oturum analizi sayfasındaki notlar bölümüne uyguladıkları tekniklerin isimlerini yazacaklar. Bunun için notlar bölümüne ek olarak "Uygulanan Teknikler" isimli bir bölüm oluşturabiliriz. Danışan tarafından teknik girildiyse bu teknikler oturum analizi raporunda "Uygulanan Teknikler" bölümünde listelenmeli ve raporlamanın bir parçası olmalı. Eğer danışan tarafından teknik girilmemişse bu bölüm raporda yer almamalıdır. Danışan tarafından uygulanan bir teknik öneri olarak sunulmamalıdır.