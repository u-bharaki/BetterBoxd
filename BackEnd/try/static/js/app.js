// --- GLOBAL DEĞİŞKENLER ---
window.currentProductionId = "c79d4af6-0214-44cb-b1d4-923b166c68da"; // Sayfada açık olan film (Varsayılan 1)
window.activeProductionId = null; // Modalda işlem yapılan film

// --- PLACEHOLDER LINKLERI ---
const IMG_FALLBACK = {
    POSTER: 'https://placehold.co/200x300?text=No+Poster',
    BACKDROP: 'https://placehold.co/1500x500?text=No+Backdrop',
    AVATAR: 'https://placehold.co/100x100?text=U',
    SMALL_POSTER: 'https://placehold.co/50x75?text=No+Img'
};

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
    window.activeProductionId = prodId || window.currentProductionId;
    const modal = document.getElementById('reviewModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');

    // Modalı açarken yıldızları sıfırla
    const container = document.getElementById('modal-star-container');
    if (container) {
        container.dataset.rating = 0;
        renderStars(container, 0);
    }

    document.querySelector('.form-textarea').value = "";
}
function closeModal() {
    const modal = document.getElementById('reviewModal');
    if (modal) {
        document.getElementById('reviewModal').classList.remove('active');
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
    window.activeProductionId = null;
}

async function saveReview() {
    const ratingContainer = document.getElementById('modal-star-container');
    const score = parseInt(ratingContainer.dataset.rating || 0); // 1-10 arası
    const text = document.querySelector('.form-textarea').value;

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
            closeModal();
            await loadProduction(window.currentProductionId);
            setTimeout(() => {
                alert('İnceleme başarıyla kaydedildi!');
            }, 50);
        } else {
            alert('Hata: ' + (result.error || 'Bilinmeyen hata'));
        }
    } catch (error) {
        console.error('Hata:', error);
    }
}
// --- SVG İKONLARI (SARI ve GRİ) ---
const STAR_ICONS = {
    FULL:  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#FFC107"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>`,
    HALF:  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><defs><linearGradient id="halfGrad"><stop offset="50%" stop-color="#FFC107"/><stop offset="50%" stop-color="#4A5158"/></linearGradient></defs><path fill="url(#halfGrad)" d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>`,
    EMPTY: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#4A5158"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>`
};

function initJsStarRating(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    renderStars(container, 0);

    container.addEventListener('mousemove', (e) => {
        const score = calculateScore(e, container);
        renderStars(container, score);
    });

    container.addEventListener('mouseleave', () => {
        const savedScore = parseInt(container.dataset.rating || 0);
        renderStars(container, savedScore);
    });

    container.addEventListener('click', (e) => {
        const score = calculateScore(e, container);
        container.dataset.rating = score; // HTML'e kaydet (1-10 arası)
        renderStars(container, score);
        console.log(`Puan Verildi: ${score}`);
    });
}

function calculateScore(e, container) {
    const rect = container.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const width = rect.width;

    let percent = x / width;
    if (percent < 0) percent = 0;
    if (percent > 1) percent = 1;

    let score = Math.ceil(percent * 10);
    if (score === 0) score = 1;
    return score;
}

// For review page
function renderStars(container, score) {
    let html = '';

    const fullStars = Math.floor(score / 2);
    const hasHalf = score % 2 !== 0;
    const emptyStars = 5 - fullStars - (hasHalf ? 1 : 0);

    for (let i = 0; i < fullStars; i++) html += STAR_ICONS.FULL;
    if (hasHalf) html += STAR_ICONS.HALF;
    for (let i = 0; i < emptyStars; i++) html += STAR_ICONS.EMPTY;

    container.innerHTML = html;
}

function getStars(rating, maxRating) {
    const normalized = (rating / maxRating) * 5; // 5 yıldız sistemine normalize et
    const fullStars = Math.floor(normalized);
    const remainder = normalized % 1;

    let stars = '';

    // Tam dolu yıldızlar
    for (let i = 0; i < fullStars; i++) {
        stars += '★';
    }

    // Yarım yıldız kontrolü (0.25'ten büyükse yarım yıldız)
    if (remainder >= 0.25 && remainder < 0.75) {
        // Yarım yıldız karakteri - en uyumlu olanlar:
        //stars += '⭐'; // Seçenek 1: Emoji yıldız (en garantili)
        // stars += '✪'; // Seçenek 2: Çemberli yıldız
         stars += '⯨'; // Seçenek 3: Yarım dolu yıldız
    } else if (remainder >= 0.75) {
        // 0.75 ve üzeri ise tam yıldız say
        stars += '★';
    }

    // Boş yıldızları hesapla
    const totalFilledStars = stars.length;
    const emptyStars = 5 - totalFilledStars;

    // Boş yıldızlar
    for (let i = 0; i < emptyStars; i++) {
        stars += '☆';
    }

    return stars;
}

// --- LOAD ---

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
        document.querySelector('.production-meta span:last-child').textContent = prod.director;

        document.querySelector('.stars_imdb_rating').textContent = getStars(prod.imdb_rating || 0.0, 10);
        document.querySelector('.imdb_score').textContent = prod.imdb_rating || 0.0;
        document.querySelector('.imdb_votes').textContent = `(${prod.imdb_votes || 0})`;

        document.querySelector('.stars_site_rating').textContent = getStars(prod.site_rating || 0.0, 10);
        document.querySelector('.site_score').textContent = prod.site_rating || 0.0;
        document.querySelector('.site_votes').textContent = `(${prod.site_votes || 0})`;

        document.querySelector('.plot').textContent = prod.plot;

        // Resimler
        const posterEl = document.querySelector('.poster');
        const backdropEl = document.querySelector('.backdrop');

        posterEl.onerror = function () { this.src = IMG_FALLBACK.POSTER; };
        backdropEl.onerror = function () { this.src = IMG_FALLBACK.BACKDROP; };

        posterEl.src = prod.poster || IMG_FALLBACK.POSTER;
        backdropEl.src = prod.backdrop || IMG_FALLBACK.BACKDROP;

        // Alt Verileri Çek
        loadCast(id);
        loadReviews(id);

    } catch (error) {
        console.error('Film detay hatası:', error);
    }
}

async function loadAllMovies() {
    // Sayfa ilk açıldığında veya filtre değiştiğinde çalışır

    const container = document.getElementById('films-grid');
    const indicator = document.getElementById('page-indicator');

    container.innerHTML = '<p style="color:#888;">Filmler yükleniyor...</p>';

    // URL Parametrelerini Oluştur (örn: /api/productions?page=2&genres=Action&sort=rating)
    const params = new URLSearchParams({
        page: currentFilters.page,
        genres: currentFilters.genres,
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
            container.innerHTML = '<p class="col-span-full text-gray-500 text-center">Bu kriterlere uygun film bulunamadı.</p>';
            return;
        }

        // Filmleri Ekrana Bas
        data.productions.forEach(movie => {
            // Poster yoksa varsayılan resim
            const poster = movie.poster || IMG_FALLBACK.POSTER;

            const html = `
                <div class="group relative cursor-pointer" onclick="loadProduction('${movie.id}'); navigateTo('production')">
                    <div class="relative overflow-hidden rounded-xl border border-[#3A424A] group-hover:border-[#FFC107] transition-all">
                        <img src="${poster}" 
                             onerror="this.onerror=null;this.src='${IMG_FALLBACK.POSTER}'"
                             class="w-full aspect-[2/3] object-cover transform group-hover:scale-105 transition duration-300">
                                                
                        <!-- Puan Rozeti -->
                        <div class="absolute top-2 right-2 bg-black/80 text-[#FFC107] px-2 py-1 rounded text-xs font-bold shadow-lg backdrop-blur-sm">
                            ★ ${movie.rating}
                        </div>
                        
                        <!-- Hover Efekti (Karartma) -->
                        <div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all duration-300"></div>
                    </div>
                    
                    <div class="mt-3">
                        <h4 class="text-white font-bold text-sm truncate group-hover:text-[#FFC107] transition">${movie.title}</h4>
                        <span class="text-gray-500 text-xs">${movie.year}</span>
                    </div>
                </div>
            `;
            container.innerHTML += html;
        });

        // Sayfa Göstergesini Güncelle
        if (indicator) indicator.textContent = `Sayfa ${data.current_page} / ${data.total_pages}`;
    } catch (error) {
        console.error('Filmler yüklenirken hata:', error);
        container.innerHTML = '<p class="text-red-500 col-span-full text-center">Yükleme hatası.</p>';
    }
}

async function loadCast(id) {
    const response = await fetch(`/api/production/${id}/cast`);
    const castData = await response.json();
    const castList = castData.cast;

    const grid = document.querySelector('.cast-grid');
    grid.innerHTML = '';

    castList.forEach(actor => {
        grid.innerHTML += `
            <div class="cast-card text-center">
                <div class="w-24 h-24 mx-auto mb-2 rounded-full overflow-hidden bg-[#333] border-2 border-[#3A424A]">
                     <!-- Oyuncu resmi yoksa baş harfini gösterelim veya placeholder -->
                     <img src="${IMG_FALLBACK.AVATAR}" onerror="this.src='${IMG_FALLBACK.AVATAR}'" class="w-full h-full object-cover">
                </div>
                <div class="text-white font-bold text-sm">${actor.name}</div>
            </div>
        `;
    });
}

async function loadReviews(id) {
    const response = await fetch(`/api/production/${id}/reviews`);
    const reviews = await response.json();

    // 2. Tab (İncelemeler) içeriğini bul
    const container = document.querySelectorAll('.tab-content')[1];
    container.innerHTML = '<h2 class="section-title text-2xl font-bold text-white mb-6">Son İncelemeler</h2>';

    if (reviews.length === 0) {
        container.innerHTML += '<p style="color:#888">Henüz inceleme yok.</p>';
        return;
    }

    reviews.forEach(r => {
        // Yıldız sayısını hesapla (Puan / 2)
        const starCount = Math.round(r.score / 2);
        const starsStr = '★'.repeat(starCount) + '☆'.repeat(5 - starCount);

        container.innerHTML += `
            <div class="bg-[#2C343A] p-6 rounded-xl mb-4 border border-[#3A424A]">
                <div class="flex items-center gap-4 mb-3">
                    <div class="w-10 h-10 rounded-full bg-[#FFC107] flex items-center justify-center font-bold text-[#14181C]">
                        ${r.author.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <div class="text-white font-bold">${r.author}</div>
                        <div class="text-[#FFC107] text-sm">${starsStr} (${r.score}/10)</div>
                    </div>
                </div>
                <div class="text-gray-300 font-serif leading-relaxed">${r.text}</div>
            </div>
        `;
    });
}

async function loadFeed() {
    const container = document.getElementById('feed-container');
    container.innerHTML = '<p class="text-gray-500">Yükleniyor...</p>';

    try {
        const res = await fetch('/api/feed');
        const items = await res.json();

        if (!items.length) {
            container.innerHTML = '<p class="text-gray-500">Akış boş.</p>';
            return;
        }

        let html = '';
        items.forEach(item => {
            const poster = item.poster || IMG_FALLBACK.SMALL_POSTER;
            html += `
                <div class="bg-[#2C343A] p-4 mb-4 rounded-lg flex gap-4 border border-[#3A424A]">
                    <img src="${poster}" 
                         onerror="this.onerror=null;this.src='${IMG_FALLBACK.SMALL_POSTER}'"
                         class="w-16 h-24 object-cover rounded cursor-pointer hover:opacity-80 transition" 
                         onclick="loadProduction('${item.production_id}'); navigateTo('production')">
                    <div>
                        <div class="text-gray-400 text-sm mb-1"><strong>${item.user}</strong> izledi:</div>
                        <h3 class="text-white font-bold text-lg">${item.title}</h3>
                        <div class="text-[#FFC107] text-sm mb-2">★ ${item.score}</div>
                        <p class="text-gray-300 font-serif text-sm">${item.review}</p>
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;
    } catch (e) {
        console.error(e);
    }
}

async function updateSettings() {
    const new_username = document.getElementById("settings-username").value;
    const new_email = document.getElementById("settings-email").value;

    const old_password = document.getElementById("current-password").value;
    const new_password = document.getElementById("new-password").value;
    const new_password2 = document.getElementById("confirm-password").value;

    const msg = document.getElementById("settings-message");
    msg.textContent = "İşlem yapılıyor...";


    try {
        const res = await fetch("/api/update_settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                new_username,
                new_email,
                old_password,
                new_password,
                new_password2
            })
        });

        const data = await res.json();

        msg.textContent = data.success ? "✅ " + data.message : "❌ " + data.message;

    } catch (e) {
        console.error("Update error:", e);
        msg.textContent = "❌ Sunucuya ulaşılamadı.";
    }
}

let ratingChartInstance = null;
let genreChartInstance = null;

async function loadProfile(user_id = null) {
    try {

        url = user_id ? `/api/profile/${user_id}` : '/api/profile';

        const response = await fetch(url);
        const data = await response.json();

        if(data.error) {
            alert("Kullanıcı bulunamadı");
            return;
        }

        window.currentProfileId = data.user_id

        // İstatistikleri Yaz
        document.getElementById('profile-fullname').textContent = data.fullname;
        document.getElementById('profile-username').textContent = '@' + data.username;
        document.getElementById('stat-watched').textContent = data.stats.watched;
        document.getElementById('stat-lists').textContent = data.stats.lists;
        document.getElementById('stat-following').textContent = data.stats.following;
        document.getElementById('stat-followers').textContent = data.stats.followers;

        // Son Aktiviteleri Listele
        const activityContainer = document.getElementById('profile-recent-activity');
        if (data.recent_activity.length === 0) {
            activityContainer.innerHTML = '<p class="text-gray-500 text-center py-4">Henüz aktivite yok.</p>';
        } else {
            let html = '';
            data.recent_activity.forEach(act => {
                const poster = act.poster || 'https://placehold.co/50x75?text=No+Img';
                html += `
                    <div class="flex gap-3 mb-4 border-b border-[#3A424A] pb-3 last:border-0">
                        <img src="${poster}" class="w-12 h-16 object-cover rounded">
                        <div>
                            <div class="text-white font-bold text-sm truncate w-40">${act.title}</div>
                            <div class="text-[#FFC107] text-xs">★ ${act.score}</div>
                            <p class="text-gray-400 text-xs mt-1 line-clamp-2">${act.text || ''}</p>
                        </div>
                    </div>`;
            });
            activityContainer.innerHTML = html;
        }

        // Grafikleri Çiz
        renderProfileCharts(data.charts);

    } catch (e) {
        console.error("Profil hatası:", e);
    }
}

function renderProfileCharts(chartData) {
    // Grafik 1: Puanlar
    const ctxRating = document.getElementById('userRatingChart');
    if (ctxRating) {
        if (ratingChartInstance) ratingChartInstance.destroy();
        ratingChartInstance = new Chart(ctxRating.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
                datasets: [{ label: 'Puanlar', data: chartData.rating_data, backgroundColor: '#FFC107', borderRadius: 4 }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { grid: { color: '#2C343A' } }, x: { grid: { display: false } } }
            }
        });
    }

    // Grafik 2: Türler
    const ctxGenre = document.getElementById('userGenreChart');
    if (ctxGenre) {
        if (genreChartInstance) genreChartInstance.destroy();
        if (chartData.genre_data.length > 0) {
            genreChartInstance = new Chart(ctxGenre.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: chartData.genre_labels,
                    datasets: [{
                        data: chartData.genre_data,
                        backgroundColor: ['#FFC107', '#3498db', '#2ecc71', '#e74c3c', '#9b59b6'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { position: 'right', labels: { color: '#E0E0E0' } } }
                }
            });
        }
    }
}

let currentFilters = {
    page: 1,
    genres: 'all',
    year: 'all',
    sort: 'pop',
    letter: 'all'
};

// ----- LISTS -----
async function loadMyLists() {
    const container = document.getElementById('lists-container')
    container.innerHTML = '<p class="text-gary-500">Listeler Yükleniyor...</p>';

    try {
        const response = await fetch('/api/my-lists')
        if (!response.ok) throw new Error("Sunucu hatası");
        const lists = await response.json()
        if (lists.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-10 bg-[#2C343A] rounded-xl border border-dashed border-gray-600">
                    <p class="text-gray-400 mb-4">Henüz hiç listen yok.</p>
                    <button onclick="createNewList()" class="text-[#FFC107] font-bold hover:underline">İlk listeni oluştur!</button>
                </div>
            `;
            return;
        }

        let html = '';
        let hasRendered = false;

        for (const list of lists) {
            try {
                if (!list.id || !list.name) {
                    console.warn("Eksik veri: Listede ID veya isim yok.")
                    continue;
                }

                html += `
                    <div class="group relative bg-[#2C343A] p-6 rounded-xl border border-[#3A424A] hover:border-[#FFC107] transition-all hover:shadow-lg hover:shadow-yellow-900/10"
                        onclick="handleListCardClick(event, '${list.id}')">

                        <!-- 1. SİLME BUTONU (Sağ Üst Köşe - Çarpı) -->
                        <button onclick="deleteList('${list.id}')"
                                class="absolute top-3 right-3 text-gray-500 hover:text-red-500 hover:bg-red-900/20 w-8 h-8 rounded-full flex items-center justify-center transition opacity-0 group-hover:opacity-100"
                                title="Listeyi Sil">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>

                        <!-- 2. BAŞLIK VE DÜZENLEME ALANI -->
                        <div class="mb-4 pr-8"> <!-- Sağdan padding bıraktık ki çarpı butonuna değmesin -->

                            <!-- GÖRÜNEN KISIM (Başlık + Kalem) -->
                            <div id="title-box-${list.id}"
                                 class="flex items-center gap-2 cursor-pointer group/edit z-10 relative"
                                 onclick="enableEdit(event, '${list.id}')">

                                <h3 class="text-xl font-bold text-white truncate">${list.name}</h3>

                                <!-- Kalem İkonu (Sadece üzerine gelince çıkar) -->
                                <span class="text-[#FFC107] opacity-0 group-hover/edit:opacity-100 transition text-sm">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                    </svg>
                                </span>
                            </div>

                            <!-- DÜZENLEME KISMI (Gizli Input) -->
                            <input type="text"
                                   id="input-${list.id}"
                                   value="${list.name}"
                                   class="hidden w-full bg-[#1C2329] text-white border border-[#FFC107] rounded px-2 py-1 outline-none font-bold text-xl"
                                   onkeydown="handleEditKeydown(event, '${list.id}')"
                                   onblur="cancelEdit('${list.id}')">
                                   <!-- onblur: Dışarı tıklayınca iptal et/kaydet -->
                        </div>

                        <p class="text-gray-500 text-sm">Bu listede ${list.production_count} yapım var.</p>
                    </div>
                `;
                hasRendered = true;
            } catch (e) {
                console.error("Render hatası: ", e, "Hatalı liste objesi: ", list)
            }
        }
        container.innerHTML = html;

        if (!hasRendered && lists.length > 0) {
            container.innerHTML = '<p class="text-red-500">Listeler render edilirken bir hata oluştu. Detaylar için konsola bakınız.</p>';
        }

    } catch (e) {
        console.error("Hata: ", e);
        container.innerHTML = '<p class="text-red-500">Listeler yüklenemedi.</p>';
    }
}

function enableEdit(event, listId) {
    event.stopPropagation();
    // Başlık divini gizle
    document.getElementById(`title-box-${listId}`).classList.add('hidden');

    // Inputu göster ve odaklan
    const input = document.getElementById(`input-${listId}`);
    input.classList.remove('hidden');
    input.focus();
    // İmleci sona getirmek için
    const val = input.value;
    input.value = '';
    input.value = val;
}

function handleEditKeydown(event, listId) {
    if (event.key === 'Enter') {
        const newName = event.target.value;
        saveListName(listId, newName);
        event.target.blur(); // Inputtan çık (bu da onblur'u tetikler ama saveListName zaten işi yapmış olur)
    } else if (event.key === 'Escape') {
        cancelEdit(listId);
    }
}

function cancelEdit(listId) {
    document.getElementById(`title-box-${listId}`).classList.remove('hidden');
    document.getElementById(`input-${listId}`).classList.add('hidden');
}

async function saveListName(listId, newName) {
    if (!newName.trim()) {
        alert("İsim boş olamaz");
        cancelEdit(listId);
        return;
    }

    try {
        const response = await fetch(`/api/list/${listId}/update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }, // Düzeltilmiş header
            body: JSON.stringify({ name: newName })
        });

        const result = await response.json();

        if (result.success) {
            // Tüm listeyi yeniden yükle ki her şey tazelensin
            loadMyLists();
        } else {
            alert("Hata: " + result.error);
            cancelEdit(listId);
        }
    } catch (e) {
        console.error(e);
    }
}

async function deleteList(listId) {
    if (!confirm("Bu listeyi silmek istediğine emin misin?")) return;

    try {
        const response = await fetch(`/api/list/${listId}/delete`, { method: 'POST' });
        const result = await response.json();

        if (result.success) {
            loadMyLists();
        } else {
            alert("Hata: " + result.error);
        }
    } catch (e) {
        console.error(e);
    }
}

async function createNewList() {
    const name = prompt("Yeni listenin adı ne olsun?");

    if (!name) return;

    try {
        const response = await fetch('/api/list/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ list_name: name})
        });
        const result = await response.json();

        if (result.success) {
            loadMyLists();
        } else {
            alert("Hata: " + result.error);
        }
    } catch (e) {
        console.error(e);
    }
}

async function loadListDetails(listId) {
    navigateTo('list-detail');

    const titleEl = document.getElementById('detail-list-name');
    const countEl = document.getElementById('detail-list-count');
    const gridEl = document.getElementById('list-detail-grid');

    titleEl.textContent = "Yükleniyor...";
    gridEl.innerHTML = '';

    try {
        const response = await fetch(`/api/list/${listId}/productions`);
        const data = await response.json();

        titleEl.textContent = data.list_name;
        countEl.textContent = `${data.productions.length} Yapım`;

        if (data.productions.length === 0) {
            gridEl.innerHTML = '<p class="col-span-full text-gray-500 text-center py-10">Bu listede henüz yapım yok.</p>';
            return;
        }

        data.productions.forEach(prod => {
            const poster = prod.poster || IMG_FALLBACK.POSTER;

            gridEl.innerHTML += `
                <div class="group relative">
                    <!-- Film Kartı -->
                    <div class="cursor-pointer" onclick="loadProduction('${prod.id}'); navigateTo('production')">
                        <img src="${poster}"
                         onerror="this.onerror=null;this.src='${IMG_FALLBACK.POSTER}'"
                         class="w-full aspect-[2/3] object-cover rounded-lg border border-[#3A424A] hover:border-[#FFC107] transition">
                        <h4 class="text-white text-sm font-bold mt-2 truncate">${prod.title}</h4>
                        <span class="text-gray-500 text-xs">${prod.year}</span>
                    </div>

                    <!-- Hızlı Menü (3 Nokta) - İstersen buraya da modal açma özelliği koyabilirsin -->
                    <button onclick="openListSelectionModal('${prod.id}')" 
                            class="absolute top-2 right-2 bg-black/60 text-white w-8 h-8 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 hover:bg-[#FFC107] hover:text-black transition backdrop-blur-sm z-10">
                        +
                    </button>
                </div>
            `;
        });
    } catch (e) {
        console.error(e);
        titleEl.textContent = "Hata";
    }
}

async function openListSelectionModal(prodId) {
    const targetProdId = prodId || window.currentProductionId;
    window.activeModalProductionId = targetProdId;

    const modal = document.getElementById('listSelectionModal');
    const container = document.getElementById('list-selection-container');

    modal.classList.remove('hidden');
    modal.classList.add('flex');
    container.innerHTML = '<p class="text-gray-400 text-center">Listeler getiriliyor...</p>';

    try {
        const response = await fetch(`/api/list/${targetProdId}/lists_status`);
        const lists = await response.json();
        container.innerHTML = '';
        if (lists.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center text-sm">Hiç listen yok. Aşağıdan oluşturabilirsin.</p>';
        }

        lists.forEach(list => {
            const isChecked = list.has_production ? 'checked' : '';

            container.innerHTML += `
                <label class="flex items-center justify-between p-3 bg-[#1C2329] rounded-lg hover:bg-[#3A424A] cursor-pointer transition border border-transparent hover:border-gray-600">
                    <span class="text-white font-medium truncate pr-4">${list.name}</span>
                    <input type="checkbox" 
                           class="w-5 h-5 accent-[#FFC107] rounded cursor-pointer" 
                           ${isChecked}
                           onchange="toggleProductionInList('${list.id}', '${targetProdId}', this)">
                </label>
            `;
        });
    } catch (e) {
        console.error(e);
        container.innerHTML = '<p class="text-red-500 text-center">Hata oluştu.</p>';
    }
}

async function toggleProductionInList(listId, prodId, checkbox) {
    checkbox.disabled = true;

    try {
        const response = await fetch(`/api/list/${listId}/toggle_production`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ production_id: prodId })
        });

        const result = await response.json();

        if (!result.success) {
            alert("İşlem başarısız: " + result.error);
            checkbox.checked = !checkbox.checked;
        }
    } catch (e) {
        console.error(e);
        checkbox.checked = !checkbox.checked;
    } finally {
        checkbox.disabled = false;
    }
}

function closeListModal() {
    const modal = document.getElementById('listSelectionModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

// Modal içinden hızlı liste oluşturma
async function createNewListFromModal() {
    const name = prompt("Yeni liste adı:");
    if(!name) return;

    try {
        const response = await fetch('/api/list/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ list_name: name })
        });
        if(response.ok) {
            openListSelectionModal(window.activeModalProductionId);
        }
    } catch(e) { console.error(e); }
}

// Filtre değişince (Dropdown'lar tetikler)
function changeFilter() {
    currentFilters.genres = document.getElementById('filter-genres').value;
    currentFilters.year = document.getElementById('filter-year').value;
    currentFilters.sort = document.getElementById('sort-by').value;

    // Filtre değişince sayfa 1'e dönmeli
    currentFilters.page = 1;
    loadAllMovies();
}

// Sayfa değişince (Önceki/Sonraki butonları tetikler)
function changePage(direction) {
    const newPage = currentFilters.page + direction;

    // Sayfa 1'den küçük olamaz
    if (newPage < 1) return;

    currentFilters.page = newPage;
    loadAllMovies();

    // Sayfa başına kaydır
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function handleListCardClick(event, listId) {
    // Tıklanan eleman (event.target) bir butonun veya inputun içindeyse dur.
    if (event.target.closest('button') || event.target.closest('input')) {
        return;
    }

    // Değilse, detay sayfasına git
    loadListDetails(listId);
}

// --- UI EVENTS ---
function toggleLike() {
    const btn = document.getElementById('likeBtn');
    btn.classList.toggle('active');
    btn.innerHTML = btn.classList.contains('active') ? '♥ Beğenildi' : '♡ Beğen';
}

function openTab(event, tabId) {
    // 1. TÜM İÇERİKLERİ GİZLE
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
        content.classList.remove('block');
    });

    // 2. TÜM BUTONLARI PASİF YAP (Griye çevir)
    document.querySelectorAll('.tab-btn').forEach(btn => {
        // Aktif stilleri sök
        btn.className = "tab-btn text-gray-500 hover:text-gray-300 py-4 font-medium transition cursor-pointer";
    });

    // 3. SEÇİLEN İÇERİĞİ GÖSTER
    document.getElementById(tabId).classList.remove('hidden');
    document.getElementById(tabId).classList.add('block');

    // 4. TIKLANAN BUTONU AKTİF YAP (Sarı yap)
    // event.currentTarget tıklanan butondur
    event.currentTarget.className = "tab-btn active text-[#FFC107] border-b-2 border-[#FFC107] py-4 font-bold transition cursor-pointer";
}

function openProfileTab(event, tabId) {
    console.log("Tıklandı! Hedef Tab:", tabId);
    // 1. Tüm içerik kutularını gizle
    document.querySelectorAll('.profile-tab-content').forEach(content => {
        content.classList.add('hidden');
        content.classList.remove('block');
    });

    // 2. Tüm tab butonlarını pasif (Gri) yap
    document.querySelectorAll('.profile-tab-btn').forEach(btn => {
        btn.classList.remove('text-[#FFC107]', 'border-b-2', 'border-[#FFC107]', 'font-bold', 'active');
        btn.classList.add('text-gray-500', 'font-medium');
    });

    // 3. İstenen kutuyu aç (Hedef)
    const targetContent = document.getElementById(tabId);
    if (targetContent) {
        targetContent.classList.remove('hidden');
        targetContent.classList.add('block');
    }

    // 4. Eğer tıklanan şey bir Tab Butonuysa onu Sarı yap
    if (event && event.currentTarget && event.currentTarget.classList.contains('profile-tab-btn')) {
        event.currentTarget.classList.remove('text-gray-500', 'font-medium');
        event.currentTarget.classList.add('text-[#FFC107]', 'border-b-2', 'border-[#FFC107]', 'font-bold', 'active');
    }

    const userId = 1;

    if (tabId === 'tab-followers') {
        console.log("Takipçiler çekiliyor...");
        loadFollowers(userId);
    } else if (tabId === 'tab-following') {
        console.log("Takip edilenler çekiliyor...");
        loadFollowing(userId);
    }
}

// --- KULLANICI LİSTESİ MODALI (Takipçi/Takip Edilen) ---

function openUserListModal(type) {
    const modal = document.getElementById('userListModal');
    const title = document.getElementById('userListModalTitle');
    const container = document.getElementById('userListModalContainer');

    // Modalı Aç
    modal.classList.remove('hidden');
    modal.classList.add('flex');

    // Yükleniyor mesajı
    container.innerHTML = '<p class="text-gray-400 text-center py-4">Yükleniyor...</p>';

    const userId = window.currentProfileId || 1;

    if (type === 'followers') {
        title.textContent = 'Takipçiler';
        fetchUserList(userId, 'followers', container);
    } else {
        title.textContent = 'Takip Edilenler';
        fetchUserList(userId, 'following', container);
    }
}

function closeUserListModal() {
    const modal = document.getElementById('userListModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

async function fetchUserList(userId, type, container) {
    try {
        const response = await fetch(`/api/user/${userId}/${type}`);
        const users = await response.json();

        container.innerHTML = '';

        if (users.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center text-sm py-4">Liste boş.</p>';
            return;
        }

        users.forEach(user => {
            // Dikey Liste Elemanı Tasarımı
            container.innerHTML += `
                <div class="flex items-center gap-3 p-3 bg-[#1C2329] rounded-lg hover:bg-[#3A424A] transition border border-transparent hover:border-gray-600 cursor-pointer"
                    onclick="loadProfile('${user.id}'); closeUserListModal()">
                    <!-- Avatar -->
                    <div class="w-10 h-10 bg-[#FFC107] rounded-full flex items-center justify-center font-bold text-[#14181C] text-sm shrink-0">
                        ${user.username.charAt(0).toUpperCase()}
                    </div>
                    
                    <!-- İsim Bilgileri -->
                    <div class="overflow-hidden">
                        <h4 class="text-white font-bold text-sm truncate">${user.first_name} ${user.last_name}</h4> 
                        <p class="text-gray-400 text-xs truncate">@${user.username}</p>
                    </div>
                </div>
            `;
        });

    } catch (e) {
        console.error(e);
        container.innerHTML = '<p class="text-red-500 text-center text-sm">Hata oluştu.</p>';
    }
}

// Kullanıcı Kartı HTML Şablonu
function createUserCard(user) {
    return `
        <div class="flex items-center gap-4 bg-[#2C343A] p-4 rounded-lg border border-[#3A424A] hover:border-[#FFC107] transition cursor-pointer">
            <div class="w-12 h-12 bg-[#FFC107] rounded-full flex items-center justify-center font-bold text-[#14181C] text-lg shrink-0">
                ${user.username.charAt(0).toUpperCase()}
            </div>
            <div class="overflow-hidden">
                <h4 class="text-white font-bold truncate">${user.first_name} ${user.last_name}</h4>
                <p class="text-gray-400 text-sm truncate">@${user.username}</p>
            </div>
        </div>
    `;
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
        html += `<button onclick="filterByLetter('${char}')" class="px-3 py-1 rounded hover:bg-[#FFC107] hover:text-black transition ${currentFilters.letter === char ? 'bg-[#FFC107] text-black font-bold' : 'text-gray-400 font-medium'}">${char}</button>`;
    })

    container.innerHTML = html;
}

function filterByLetter(char) {
    currentFilters.letter = char;
    currentFilters.page = 1;

    loadAllMovies();
    initAlphaBar();
}

// SEARCH
let searchTimeout;

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('global-search-input');
    const resultsDropdown = document.getElementById('search-results-dropdown');

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            clearTimeout(searchTimeout);

            if (query.length < 2) {
                resultsDropdown.classList.add('hidden');
                resultsDropdown.innerHTML = '';
                return;
            }

            searchTimeout = setTimeout(() => {
                performSearch(query);
            }, 300);
        });

        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !resultsDropdown.contains(e.target)) {
                resultsDropdown.classList.add('hidden');
            }
        });
    } else {
        console.error("HATA: 'global-search-input' ID'li element bulunamadı! HTML'i kontrol et.");
    }
});

async function performSearch(query) {
    const resultsDropdown = document.getElementById('search-results-dropdown');

    if (!resultsDropdown) {
        console.error("HATA: Dropdown kutusu (ID: search-results-dropdown) HTML'de bulunamadı!");
        return;
    }

    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        if (!response.ok) {
            console.error(`API Hatası: ${response.status}`);
        }
        const results = await response.json();
        resultsDropdown.innerHTML = '';

        if (results.length === 0) {
            resultsDropdown.innerHTML = '<div class="p-4 text-gray-500 text-sm text-center">Sonuç bulunamadı.</div>';
        } else {
            results.forEach(production => {
                const poster = production.poster || IMG_FALLBACK.SMALL_POSTER;
                const ratingHtml = production.imdb_rating ? `<span class="text-[#FFC107] text-xs">★ ${production.imdb_rating}</span>` : '';

                const html = `
                    <div class="flex items-center gap-3 p-3 hover:bg-[#2C343A] cursor-pointer transition border-b border-[#3A424A] last:border-none group"
                         onclick="loadProduction('${production.id}'); navigateTo('production'); document.getElementById('search-results-dropdown').classList.add('hidden'); document.getElementById('global-search-input').value = '';">
                        <img src="${poster}" 
                             onerror="this.onerror=null;this.src='${IMG_FALLBACK.SMALL_POSTER}'"
                             class="w-10 h-14 object-cover rounded shadow-sm border border-[#3A424A] group-hover:border-[#FFC107]">
                        <div>
                            <h4 class="text-white font-bold text-sm group-hover:text-[#FFC107] transition">${production.title}</h4>
                            <div class="flex items-center gap-2">
                                <span class="text-gray-500 text-xs">${production.year}</span>
                                ${ratingHtml}
                            </div>
                        </div>
                    </div>
                `;
                resultsDropdown.innerHTML += html;
            });
        }
        resultsDropdown.classList.remove('hidden');
    } catch (e) {
        console.error("Arama hatası: ", e);
    }
}

// --- BAŞLATMA (INIT) ---
document.addEventListener('DOMContentLoaded', () => {
    // Yıldız sistemlerini başlat
    initJsStarRating('page-star-container');
    initJsStarRating('modal-star-container');
    initAlphaBar();

    // Varsayılan filmi yükle
    loadAllMovies();

    // Modal dışına tıklayınca kapat
    document.getElementById('reviewModal').addEventListener('click', function(e) {
        if (e.target === this) closeModal();
    });
});
