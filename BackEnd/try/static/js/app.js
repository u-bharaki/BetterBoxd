// --- GLOBAL DEĞİŞKENLER ---
window.currentProductionId = "c79d4af6-0214-44cb-b1d4-923b166c68da"; // Sayfada açık olan film (Varsayılan 1)
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

async function loadAllMovies() {
    // Sayfa ilk açıldığında veya filtre değiştiğinde çalışır

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
                <div class="group relative cursor-pointer" onclick="loadProduction('${movie.id}'); navigateTo('production')">
                    <div class="relative overflow-hidden rounded-xl border border-[#3A424A] group-hover:border-[#FFC107] transition-all">
                        <img src="${poster}" class="w-full aspect-[2/3] object-cover transform group-hover:scale-105 transition duration-300">
                        
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
        container.innerHTML = '<p class="text-red-500">Yükleme hatası.</p>';
    }
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

async function loadProfile() { /* Aynısı kalsın... */ }

let currentFilters = {
    page: 1,
    genre: 'all',
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
                                 class="flex items-center gap-2 cursor-pointer group/edit" 
                                 onclick="enableEdit('${list.id}')">
                                
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

// 1. Düzenleme Modunu Aç
function enableEdit(listId) {
    // Başlık divini gizle
    document.getElementById(`title-box-${listId}`).classList.add('hidden');

    // Inputu göster ve odaklan
    const input = document.getElementById(`input-${listId}`);
    input.classList.remove('hidden');
    input.focus();
    // İmleci sona getirmek için küçük bir hack
    const val = input.value;
    input.value = '';
    input.value = val;
}

// 2. Tuşlara Basılınca (Enter = Kaydet, Esc = İptal)
function handleEditKeydown(event, listId) {
    if (event.key === 'Enter') {
        const newName = event.target.value;
        saveListName(listId, newName);
        event.target.blur(); // Inputtan çık (bu da onblur'u tetikler ama saveListName zaten işi yapmış olur)
    } else if (event.key === 'Escape') {
        cancelEdit(listId);
    }
}

// 3. Düzenlemeyi İptal Et (Veya dışarı tıklayınca kaydet)
function cancelEdit(listId) {
    // Burada tercih senin: Dışarı tıklayınca kaydetsin mi iptal mi etsin?
    // Modern UX genelde "dışarı tıklayınca kaydet" şeklindedir.
    // Eğer iptal etsin istersen sadece sınıfları değiştir.

    const input = document.getElementById(`input-${listId}`);
    const newName = input.value.trim();

    // Eğer isim değişmişse ve boş değilse kaydetmeyi dene
    // (Not: Basit olması için burada direkt eski haline döndürüyoruz,
    // kaydetmeyi sadece Enter ile yapmak daha güvenli olabilir karışıklığı önlemek için)

    // Şimdilik sadece görünümü eski haline getiriyoruz (Esc basmış gibi)
    document.getElementById(`title-box-${listId}`).classList.remove('hidden');
    input.classList.add('hidden');
}

// 4. İsmi Sunucuya Kaydet
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

// 5. Silme (Artık çarpı butonu çağırıyor)
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
            const poster = prod.poster || 'https://via.placeholder.com/200x300';

            gridEl.innerHTML += `
                <div class="group relative">
                    <!-- Film Kartı -->
                    <div class="cursor-pointer" onclick="loadProduction('${prod.id}'); navigateTo('production')">
                        <img src="${poster}" class="w-full aspect-[2/3] object-cover rounded-lg border border-[#3A424A] hover:border-[#FFC107] transition">
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
        } else {
            console.log(result.action === 'added' ? 'Eklendi' : 'Çıkarıldı');
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
            body: JSON.stringify({ name: name })
        });
        if(response.ok) {
            openListSelectionModal(window.activeModalProductionId);
        }
    } catch(e) { console.error(e); }
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
    loadAllMovies();

    // Modal dışına tıklayınca kapat
    document.getElementById('reviewModal').addEventListener('click', function(e) {
        if (e.target === this) closeModal();
    });
});
