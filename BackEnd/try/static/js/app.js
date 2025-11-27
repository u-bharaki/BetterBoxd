// --- GLOBAL DEĞİŞKENLER ---
window.currentProductionId = 1; // Sayfada açık olan film (Varsayılan 1)
window.activeProductionId = null; // Modalda işlem yapılan film

// --- SAYFA YÖNLENDİRME (ROUTING) ---
function navigateTo(pageName) {
    // Sayfaları Gizle/Göster
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    const targetPage = document.getElementById(pageName + '-page');
    if (targetPage) targetPage.classList.add('active');

    // Dropdown kapat
    const dropdown = document.getElementById('profileDropdown');
    if(dropdown) dropdown.classList.remove('active');

    // Verileri Yükle
    if (pageName === 'feed') loadFeed();
    else if (pageName === 'lists') loadMyLists();
    else if (pageName === 'profile') loadProfile();
    else if (pageName === 'films') loadAllMovies();
}

// --- MODAL VE REVIEW İŞLEMLERİ ---

function openModal(prodId) {
    // Eğer bir ID gelirse onu kullan, yoksa o an sayfadaki filmi kullan
    window.activeProductionId = prodId || window.currentProductionId;

    const modal = document.getElementById('reviewModal');
    modal.classList.add('active');

    // Modalı açarken eski puanları sıfırla
    const stars = modal.querySelectorAll('.star');
    stars.forEach(s => s.classList.remove('filled'));
    document.getElementById('modalRating').dataset.currentRating = "0";
    document.querySelector('.form-textarea').value = ""; // Texti temizle

    // Modal başlığına film ismini koyabiliriz (Opsiyonel, şimdilik sabit kalsın)
}

function closeModal() {
    document.getElementById('reviewModal').classList.remove('active');
}

async function saveReview() {
    // 1. Puanı Modalın içinden al
    const ratingContainer = document.getElementById('modalRating');
    // dataset string döner, sayıya çevir
    const score = parseInt(ratingContainer.dataset.currentRating || 0);

    // 2. Metni al
    const text = document.querySelector('.form-textarea').value;

    // 3. Kontrol
    if (score === 0) {
        alert("Lütfen bir puan verin!");
        return;
    }

    const data = {
        productionId: window.activeProductionId,
        score: score,
        text: text
    };

    try {
        const response = await fetch('/api/review', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert('İnceleme başarıyla kaydedildi!');
            closeModal();
            // Eğer o an film detay sayfasındaysak yorumları güncelle
            if (window.activeProductionId === window.currentProductionId) {
                loadProduction(window.currentProductionId);
            }
        } else {
            alert('Hata: ' + (result.error || 'Bilinmeyen bir hata oluştu. Giriş yaptınız mı?'));
        }
    } catch (error) {
        console.error('Hata:', error);
        alert('Sunucu hatası. Lütfen console logu kontrol edin.');
    }
}

// --- YILDIZ SİSTEMİ (STAR RATING) ---
function initializeStarRating(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const stars = container.querySelectorAll('.star');

    // Başlangıç değeri
    if (!container.dataset.currentRating) {
        container.dataset.currentRating = "0";
    }

    stars.forEach((star) => {
        // Hover Efekti
        star.addEventListener('mouseenter', function() {
            const value = parseInt(this.getAttribute('data-value'));
            updateVisuals(stars, value);
        });

        // Tıklama Efekti
        star.addEventListener('click', function() {
            const value = this.getAttribute('data-value');
            container.dataset.currentRating = value;
            updateVisuals(stars, parseInt(value));
        });
    });

    // Mouse Çekilince (Eski haline dön)
    container.addEventListener('mouseleave', function() {
        const saved = parseInt(this.dataset.currentRating || 0);
        updateVisuals(stars, saved);
    });

    function updateVisuals(starList, rating) {
        starList.forEach(s => {
            const val = parseInt(s.getAttribute('data-value'));
            // Puanı (1-10) kontrol et
            if (val <= rating) {
                s.classList.add('filled');
            } else {
                s.classList.remove('filled');
            }
        });
    }
}

// --- API VERİ ÇEKME İŞLEMLERİ ---

async function loadProduction(id) {
    try {
        const response = await fetch(`/api/production/${id}`);
        const prod = await response.json();

        if (prod.error) {
            console.log("Film bulunamadı");
            return;
        }

        // Global ID'yi güncelle
        window.currentProductionId = id;

        // DOM Güncelleme
        document.querySelector('.production-title').textContent = prod.title;
        document.querySelector('.production-year').textContent = prod.year;
        document.querySelector('.production-meta span').textContent = prod.director;
        document.querySelector('.rating-display span:last-child').textContent = `${prod.rating} / 10`;
        document.querySelector('.plot').textContent = prod.plot;

        // Resimler
        if(prod.poster) document.querySelector('.poster').src = prod.poster;
        if(prod.backdrop) document.querySelector('.backdrop').src = prod.backdrop;

        // Alt Verileri Çek
        loadCast(id);
        loadReviews(id);

    } catch (error) {
        console.error('Film detay hatası:', error);
    }
}

// --- FİLMLER SAYFASI LOJİĞİ ---

let currentFilters = {
    page: 1,
    genre: 'all',
    year: 'all',
    sort: 'pop',
    letter: 'all'
};

// Sayfa ilk açıldığında veya filtre değiştiğinde çalışır
async function loadAllMovies() {
    const container = document.getElementById('films-grid');
    const indicator = document.getElementById('page-indicator');

    container.innerHTML = '<p style="color:#888;">Filmler yükleniyor...</p>';

    // URL Parametrelerini Oluştur (örn: /api/productions?page=2&genre=Action&sort=rating)
    const params = new URLSearchParams({
        page: currentFilters.page,
        genre: currentFilters.genre,
        year: currentFilters.year,
        sort: currentFilters.sort,
        letter: currentFilters.letter
    });

    try {
        const response = await fetch(`/api/productions?${params}`);
        const data = await response.json();

        // Grid'i Temizle
        container.innerHTML = '';

        if (data.productions.length === 0) {
            container.innerHTML = '<p>Bu kriterlere uygun film bulunamadı.</p>';
            return;
        }

        // Filmleri Ekrana Bas
        data.productions.forEach(movie => {
            // Poster yoksa varsayılan resim
            const poster = movie.poster || 'https://via.placeholder.com/200x300?text=No+Poster';

            const html = `
                <div class="list-card" onclick="loadProduction(${movie.id}); navigateTo('production')" style="padding:0; overflow:hidden; border:none; background:transparent;">
                    <div style="position:relative;">
                        <img src="${poster}" style="width:100%; aspect-ratio: 2/3; object-fit:cover; border-radius:8px; border:1px solid #333;">
                        <div style="position:absolute; top:5px; right:5px; background:rgba(0,0,0,0.8); color:#FFC107; padding:2px 6px; border-radius:4px; font-size:12px; font-weight:bold;">
                            ★ ${movie.rating}
                        </div>
                    </div>
                    <div style="padding:10px 0; text-align:left;">
                        <h4 style="color:#fff; font-size:15px; margin-bottom:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${movie.title}</h4>
                        <span style="color:#666; font-size:13px;">${movie.year}</span>
                    </div>
                </div>
            `;
            container.innerHTML += html;
        });

        // Sayfa Göstergesini Güncelle
        indicator.textContent = `Sayfa ${data.current_page} / ${data.total_pages}`;

        // Buton durumlarını (ilk/son sayfa) yönetmek istersen burada yapabilirsin

    } catch (error) {
        console.error('Filmler yüklenirken hata:', error);
        container.innerHTML = '<p>Yükleme hatası.</p>';
    }
}

// Filtre değişince (Dropdown'lar tetikler)
function changeFilter() {
    // 1. HTML'den değerleri al
    currentFilters.genre = document.getElementById('filter-genre').value;
    currentFilters.year = document.getElementById('filter-year').value;
    currentFilters.sort = document.getElementById('sort-by').value;

    // 2. Filtre değişince sayfa 1'e dönmeli
    currentFilters.page = 1;

    // 3. Yeniden yükle
    loadAllMovies();
}

// Sayfa değişince (Önceki/Sonraki butonları tetikler)
function changePage(direction) {
    // direction: +1 (Sonraki) veya -1 (Önceki)
    const newPage = currentFilters.page + direction;

    // Sayfa 1'den küçük olamaz
    if (newPage < 1) return;

    // (Opsiyonel: Toplam sayfayı geçip geçmediğini de kontrol edebilirsin)

    currentFilters.page = newPage;
    loadAllMovies();

    // Sayfa başına kaydır
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function loadCast(id) {
    const response = await fetch(`/api/production/${id}/cast`);
    const castList = await response.json();

    const grid = document.querySelector('.cast-grid');
    grid.innerHTML = '';

    castList.forEach(actor => {
        grid.innerHTML += `
            <div class="cast-card">
                <div class="cast-image" style="background:#333; display:flex; align-items:center; justify-content:center; color:#777;">
                    ${actor.name.charAt(0)}
                </div>
                <div class="cast-name">${actor.name}</div>
                <div class="cast-role">Actor</div>
            </div>
        `;
    });
}

async function loadReviews(id) {
    const response = await fetch(`/api/production/${id}/reviews`);
    const reviews = await response.json();

    // 2. Tab (İncelemeler) içeriğini bul
    const container = document.querySelectorAll('.tab-content')[1];
    container.innerHTML = '<h2 class="section-title">Son İncelemeler</h2>';

    if (reviews.length === 0) {
        container.innerHTML += '<p style="color:#888">Henüz inceleme yok.</p>';
        return;
    }

    reviews.forEach(r => {
        // Yıldız sayısını hesapla (Puan / 2)
        const starCount = Math.round(r.score / 2);
        const starsStr = '★'.repeat(starCount) + '☆'.repeat(5 - starCount);

        container.innerHTML += `
            <div class="review-card">
                <div class="review-header">
                    <div class="review-avatar">${r.author.charAt(0).toUpperCase()}</div>
                    <div class="review-meta">
                        <div class="review-author">${r.author}</div>
                        <div class="review-date">
                            <span class="stars" style="color:#FFC107">${starsStr}</span> (${r.score}/10)
                        </div>
                    </div>
                </div>
                <div class="review-text">${r.text}</div>
            </div>
        `;
    });
}

// --- DİĞER SAYFALAR ---
async function loadFeed() {
    const container = document.getElementById('feed-container');
    container.innerHTML = 'Yükleniyor...';
    const res = await fetch('/api/feed');
    const items = await res.json();

    if(!items.length) { container.innerHTML = 'Akış boş.'; return; }

    let html = '';
    items.forEach(item => {
        html += `
            <div style="background:#2C343A; padding:15px; margin-bottom:15px; border-radius:8px; display:flex; gap:15px;">
                <img src="${item.poster}" style="width:60px; height:90px; object-fit:cover;">
                <div>
                    <div style="color:#bbb; font-size:14px;"><strong>${item.user}</strong> izledi:</div>
                    <h3 style="color:#fff;">${item.title}</h3>
                    <div style="color:#FFC107">★ ${item.score}</div>
                    <p style="color:#ddd; font-size:14px; margin-top:5px;">${item.review}</p>
                </div>
            </div>
        `;
    });
    container.innerHTML = html;
}

async function loadMyLists() { /* Aynısı kalsın... */ }
async function loadProfile() { /* Aynısı kalsın... */ }

// --- UI EVENTS ---
function toggleLike() {
    const btn = document.getElementById('likeBtn');
    btn.classList.toggle('active');
    btn.innerHTML = btn.classList.contains('active') ? '♥ Beğenildi' : '♡ Beğen';
}

function toggleWatchlist() {
    const btn = document.getElementById('watchlistBtn');
    btn.classList.toggle('active');
    btn.innerHTML = btn.classList.contains('active') ? '✓ Listede' : '+ İzleme Listesi';
}

function switchTab(index) {
    const tabs = document.querySelectorAll('.tab');
    const contents = document.querySelectorAll('.tab-content');
    tabs.forEach(t => t.classList.remove('active'));
    contents.forEach(c => c.classList.remove('active'));
    tabs[index].classList.add('active');
    contents[index].classList.add('active');
}

function toggleProfileDropdown() {
    document.getElementById('profileDropdown').classList.toggle('active');
}

function initAlphaBar() {
    const container = document.getElementById('alpha-bar');
    if(!container) return;

    const alphabet = "#ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

    // Tümü
    let html = `<button onclick="filterByLetter('all')" class="px-3 py-1 rounded hover:bg-[#FFC107] hover:text-black transition ${currentFilters.letter === 'all' ? 'bg-[#FFC107] text-black font-bold' : 'text-gray-400'}">Tümü</button>`;

    alphabet.forEach(char => {
        html += `<button onclick="filterByLetter('${char}')" class="px-3 py-1 rounded hover:bg-[#FFC107] hover:text-black transition text-gray-400 font-medium">${char}</button>`;
    })

    container.innerHTML = html;
}

function filterByLetter(char) {
    currentFilters.letter = char;
    currentFilters.page = 1;

    loadAllMovies();

    initAlphaBar();
}

// --- BAŞLATMA (INIT) ---
document.addEventListener('DOMContentLoaded', () => {
    // Yıldız sistemlerini başlat
    initializeStarRating('userRating');
    initializeStarRating('modalRating');
    initAlphaBar();

    // Varsayılan filmi yükle
    loadProduction(1);

    // Modal dışına tıklayınca kapat
    document.getElementById('reviewModal').addEventListener('click', function(e) {
        if (e.target === this) closeModal();
    });
});
