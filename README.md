# 🎬 BetterBoxd - Modern Film ve Dizi Takip Platformu

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Backend](https://img.shields.io/badge/backend-Flask-blue)
![Frontend](https://img.shields.io/badge/frontend-HTML%20%7C%20JS%20%7C%20Tailwind-red)
![Database](https://img.shields.io/badge/database-SQLite-orange)

**BetterBoxd**, sinema ve dizi tutkunları için geliştirilmiş, Letterboxd tarzı sosyal bir film keşif ve takip platformudur. Kullanıcıların izledikleri yapımları puanlayıp inceleyebileceği, kişisel listeler oluşturabileceği ve arkadaşlarıyla etkileşime girebileceği modern bir web uygulamasıdır.

Proje, **3-Tier Architecture (Üç Katmanlı Mimari)** prensiplerine uygun olarak geliştirilmiştir: veri tabanı, iş mantığı (backend) ve sunum katmanı (frontend) birbirinden bağımsız çalışır.

---

## ✨ Öne Çıkan Özellikler

### 🎥 İçerik Keşfi
- **Zengin Film Arşivi**: Binlerce film ve dizi bilgisi (yönetmen, oyuncular, özet, yıl, tür)
- **Anlık Arama**: Debounce algoritması ile sunucu dostu, anlık sonuç veren akıllı arama
- **Gelişmiş Filtreleme**: Tür, yıl, alfabetik sıralama ve popülerlik/puan bazlı filtreleme
- **IMDb Entegrasyonu**: Her yapım için IMDb puanı ve oy sayısı görüntüleme

### ⭐ Kullanıcı Etkileşimi
- **Hassas Puanlama Sistemi**: 0.5'lik adımlarla 0-5 arası detaylı puanlama (yarım yıldız desteği)
- **İnceleme Yazma**: Filmler hakkında detaylı inceleme yazabilme ve paylaşma
- **Karşılaştırmalı Puanlama**: Site ortalaması vs IMDb puanı karşılaştırması
- **Beğeni Sistemi**: Favori filmleri beğenip profilinde toplama

### 📋 Liste Yönetimi
- **Özel Listeler**: Sınırsız sayıda kişiselleştirilmiş liste oluşturma
- **CRUD İşlemleri**: Listeleri oluşturma, düzenleme, silme ve içerik yönetimi
- **Hızlı Ekleme**: Film detay sayfasından tek tıkla birden fazla listeye ekleme
- **Inline Düzenleme**: Liste adlarını sayfa yenilemeden değiştirme

### 📊 Profil ve İstatistikler
- **Görsel İstatistikler**: Chart.js ile oluşturulmuş puan dağılımı ve tür grafikleri
- **Aktivite Takibi**: İzlenen film sayısı, yazılan inceleme ve oluşturulan liste sayıları
- **Sosyal Özellikler**: Takipçi/takip edilen sistemi ve arkadaş akışı
- **Hesap Yönetimi**: Kullanıcı adı, e-posta ve şifre güncelleme

---

## 🛠️ Teknoloji Stack

### Backend
- **Python 3.x** - Ana programlama dili
- **Flask 2.x** - Lightweight web framework
- **Flask-Session** - Sunucu taraflı oturum yönetimi
- **SQLite3** - Embedded veritabanı sistemi
- **Şifre Hashleme**: SHA-256 algoritması ile güvenli şifre saklama

### Frontend
- **HTML5** - Semantic markup
- **Tailwind CSS** - Utility-first CSS framework
- **Vanilla JavaScript (ES6+)** - DOM manipulation ve API çağrıları
- **Chart.js** - İstatistik grafikleri
- **Fetch API** - Asenkron veri iletişimi

### Veritabanı Tasarımı
- **İlişkisel Model** - Normalize edilmiş tablo yapısı
- **UUID Primary Keys** - Güvenli ve benzersiz kimlikler
- **Foreign Key Constraints** - Veri bütünlüğü
- **İndeksleme** - Performans optimizasyonu

---

## 📂 Proje Yapısı

```
BetterBoxd/
│
├── BackEnd/
│   ├── databases/
│   │   └── *.db
│   ├── templates/
│   │   ├── login.html
│   │   └── register.html
│   └── try/
│   │   ├── static/
│   │   │   ├── css/
│   │   │   │   └── style.css
│   │   │   └── js/
│   │   │       └── app.js
│   │   ├── templates/
│   │   │   ├── base.html
│   │   │   ├── index.html
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   ├── appdeneme.py
│   │   ├── betterboxd.db
│   │   └── user_manager.py
│   └── requirements.txt
│
├── Data/
│   ├── databases/
│   ├── logs/
│   ├── raw_excels/
│   ├── main.py
│   ├── remove_used_tag.py
│   ├── requirements.txt
│   └── unique_film_count.py
│
└── Documents/
    ├── BIL372 AraRapor.docx
    ├── BIL372 SonRapor.docx
    ├── EER Diagramı.jpeg
    └── Relation Table.png
```

---

## 🚀 Kurulum

### Gereksinimler
- Python 3.8 veya üzeri
- pip (Python paket yöneticisi)
- Modern web tarayıcı (Chrome, Firefox, Safari, Edge)

### Adım 1: Projeyi İndirin
```bash
git clone https://github.com/u-bharaki/BetterBoxd.git
cd BetterBoxd
```

### Adım 2: Sanal Ortam Oluşturun (Önerilen)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Adım 3: Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### Adım 4: Uygulamayı Başlatın
```bash
python app.py
```

Tarayıcınızda terminalde çıkan adrese gidin.

### İlk Kullanıcı Oluşturma
1. Kayıt ol butonuna basarak register sayfasına gidin
2. Kullanıcı adı, e-posta ve şifre belirleyin
3. Giriş yapın ve keşfetmeye başlayın!

---

## 📊 Veritabanı Şeması

Proje, aşağıdaki ana tablolardan oluşur:

- **users** - Kullanıcı hesap bilgileri
- **productions** - Film ve dizi verileri
- **contributors** - Yapımlarda yer almış oyuncu, yönetmen ve yazar verileri
- **reviews** - Kullanıcı incelemeleri ve puanları
- **lists** - Kullanıcı listeleri
- **productions_in_lists** - Liste içerikleri (many-to-many)
- **follows** - Takip ilişkileri

Detaylı EER diyagramı için `Document/` klasörüne bakınız.

---

## 🎯 API Endpoints

### Kimlik Doğrulama
- `POST /login` - Kullanıcı girişi
- `POST /register` - Yeni kullanıcı kaydı
- `GET /logout` - Oturumu sonlandır

### Film İşlemleri
- `GET /api/productions` - Film listesi (filtreleme & sayfalama)
- `GET /api/production/<id>` - Film detayları
- `GET /api/search?q=<query>` - Film arama

### İnceleme ve Puanlama
- `POST /api/review` - İnceleme oluştur/güncelle
- `GET /api/reviews/<production_id>` - Film incelemelerini getir
- `POST /api/like` - Film beğen/beğeniyi kaldır

### Liste Yönetimi
- `GET /api/lists` - Kullanıcı listelerini getir
- `POST /api/list/create` - Yeni liste oluştur
- `PUT /api/list/rename` - Liste adını değiştir
- `DELETE /api/list/delete` - Liste sil
- `POST /api/list/add` - Listeye film ekle
- `POST /api/list/remove` - Listeden film çıkar

### Profil ve İstatistikler
- `GET /api/profile/stats` - Kullanıcı istatistikleri
- `GET /api/profile/activity` - Son aktiviteler
- `POST /api/settings/update` - Hesap bilgilerini güncelle

---

## 🔐 Güvenlik Özellikleri

- **Şifre Hashleme**: SHA-256 algoritması
- **Session Management**: Flask-Session ile sunucu taraflı oturum
- **SQL Injection Koruması**: Parametreli sorgular
- **XSS Koruması**: Input sanitization ve Jinja2 auto-escaping
- **CSRF Token**: Form isteklerinde güvenlik tokeni (geliştirme aşamasında)

---

## 🎨 Özellik Detayları

### Yarım Yıldız Puanlama Sistemi
Kullanıcılar filmleri 0-5 arası 0.5'lik adımlarla puanlayabilir. Sistem, CSS ve JavaScript kombinasyonu ile görsel olarak yarım yıldızları destekler:

```javascript
// 3.5 yıldız örneği
★★★⯨☆ (3.5 / 5.0)
```

### Dinamik Arama (Debounce)
Kullanıcı yazmayı bıraktıktan 300ms sonra arama tetiklenir, böylece gereksiz API çağrıları önlenir:

```javascript
let searchTimeout;
searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        performSearch(e.target.value);
    }, 300);
});
```

### Single Page Application (SPA) Yapısı
Sayfa yenilemeden içerik değişimi sağlanır:

```javascript
function navigateTo(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(page + '-page').classList.add('active');
    window.history.pushState({page}, '', `/${page}`);
}
```

---

## 👨‍💻 Geliştiriciler

**[Ali Emre YENİHAYAT]**
- GitHub: [alalayom](https://github.com/alalayom)
- LinkedIn: [linkedin.com/in/ali-emre-yenihayat-532b2b2ab/](https://www.linkedin.com/in/ali-emre-yenihayat-532b2b2ab/)
- E-posta: alalayom@gmail.com

**[Berk ÜLKER]**
- GitHub: [u-bharaki](https://github.com/u-bharaki)
- LinkedIn: [linkedin.com/in/berk--ulker/](https://www.linkedin.com/in/berk--ulker/)
- E-posta: berk.ulker.ce@gmail.com

**[Duygu AKMAN]**
- GitHub: [DUYGUAKMAN](https://github.com/DUYGUAKMAN)
- LinkedIn: [linkedin.com/in/duygu-akman-a28421259/](https://www.linkedin.com/in/duygu-akman-a28421259/)
- E-posta: duyguaakman@gmail.com

---