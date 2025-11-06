# BetterBoxd - Letterboxd Benzeri Sosyal Film Platformu

![Durum](https://img.shields.io/badge/status-geli%C5%9Ftirme%20a%C5%9Famas%C4%B1nda-yellow)
![Backend](https://img.shields.io/badge/Backend-Flask%20(Planlan%C4%B1yor)-blue)
![Database](https://img.shields.io/badge/Database-SQLite-orange)

Bu proje, **Letterboxd**'a benzer bir sosyal film ve dizi takip platformu oluşturmayı amaçlamaktadır. Kullanıcıların izledikleri yapımları puanlayıp inceleyebileceği, listeler oluşturabileceği ve birbirlerini sosyal olarak takip edebileceği bir web uygulaması hedeflenmektedir.

Proje şu anda **ilk geliştirme aşamasındadır**; veritabanı mimarisi tamamlanmış olup, backend ve frontend bileşenleri geliştirilme sürecindedir.

---

## 🚀 Proje Vizyonu ve Temel Özellikler (Planlanan)

* **🎬 Geniş Yapım Kataloğu:** Filmler ve diziler hakkında (IMDb puanı, yıl, poster, özet, oyuncular vb.) detaylı bilgilere erişim.
* **✍️ Puanlama ve Eleştiri:** Kullanıcıların izledikleri yapımlara 0-10 arası puan vermesi ve detaylı incelemeler (review) yazması.
* **👥 Sosyal Takip:** Kullanıcıların birbirini takip edebilmesi ve takip ettikleri kişilerin aktivitelerini bir "feed" üzerinde görmesi.
* **📚 Kişisel Listeleme:** "İzlenecekler", "Favorilerim", "Bitirdiklerim" gibi (UUID tabanlı) benzersiz ve kişisel listeler oluşturma.
* **🧑‍🎨 Katkıda Bulunma:** Yapımlara ait yönetmen, yazar ve oyuncu bilgilerini görme ve ilişkilendirme.

---

## 🛠️ Teknoloji Mimarisi (Mevcut ve Planlanan)

* **Backend (Planlanıyor):** **Flask**
    * RESTful API servisleri
    * Kullanıcı yönetimi (Authentication & Authorization)
    * İş mantığı (Business Logic)
* **Frontend (Planlanıyor):** [Belirlenmedi, örn: React, Jinja2 template]
* **Veritabanı (Tamamlandı):** **SQLite**
    * İlişkisel şema (`FOREIGN KEY`, `CHECK` kısıtlamaları ile veri bütünlüğü).
* **Veri İşleme (Geliştiriliyor):** **Python**
    * Harici API'lerden veri çekme, temizleme ve SQLite veritabanına yükleme betikleri.

---

## 📊 Proje Durumu (Kasım 2025)

Proje aktif olarak geliştirilmektedir.

* [✅] **Veritabanı Mimarisi:** Tüm ana tablolar (`users`, `productions`, `reviews`, `follows`, `lists`, `contributors` vb.) ve ilişkiler (`schema.sql` içinde) tanımlandı.
* [✅] **Veri Çekme Betikleri (İlk Aşama):** Harici API'den veri çeken (`main.py`) ve unique film sayısını hesaplayan (`unique_film_count.py`) Python betikleri tamamlandı.
* [⏳] **Backend (Flask API):** Geliştirilmeye başlanacak.
* [⬜] **Frontend (Web Arayüzü):** Henüz başlanmadı.

---

## 🗃️ Veritabanı Şeması

Projenin kalbi olan SQLite veritabanı, veriyi mantıksal olarak 7+ ana tabloda saklamaktadır:

1.  `users`: Kullanıcı bilgilerini tutar.
2.  `productions`: Filmler/diziler hakkındaki ana bilgileri tutar.
3.  `contributors`: Yapımlardaki kişileri (aktör, yönetmen) ve rollerini tutar.
4.  `reviews`: Kullanıcıların yapımlara verdiği puan ve yorumları saklar.
5.  `follows`: Kullanıcıların birbirini takip etme ilişkisini tutar.
6.  `lists`: Kullanıcıların oluşturduğu listelerin adını (`list_id` UUID'dir).
7.  `productions_in_lists`: Hangi yapımın hangi listeye eklendiğini gösterir.

---

## 🚀 Kurulum ve Çalıştırma (Mevcut Durum)

Projenin mevcut (veritabanı ve betik) kısmını çalıştırmak için:

### 1. Projeyi Klonlayın
```bash
git clone [https://github.com/](https://github.com/)[kullanici_adiniz]/[repo_adiniz].git
cd [repo_adiniz]
```

### 2. (Öneri) Sanal Ortam Oluşturun
```bash
# Python sanal ortamını oluştur ve aktive et
python -m venv venv
source venv/bin/activate  # (Windows için: venv\Scripts\activate)
```

### 3. Bağımlılıkları Yükleyin
Proje betiklerinin ihtiyaç duyduğu Python kütüphanelerini yükleyin.
```bash
pip install -r requirements.txt
```

### 4. Veritabanını Oluşturun
`schema.sql` (veya şema dosyanızın adı) dosyasını kullanarak SQLite veritabanı dosyasını (`proje.db` gibi) oluşturun.
```bash
# schema.sql dosyasını okuyup proje.db adında bir veritabanı oluşturur
sqlite3 proje.db < schema.sql
```

### 5. Betikleri Çalıştırın
Veritabanını harici API'den gelen verilerle doldurun ve analizleri çalıştırın.

**API'den Veri Çekme:**
```bash
python main.py
```

**Benzersiz Film Sayısını Hesaplama:**
```bash
python unique_film_count.py
```
