const BACKEND = "https://geo-ai-agent-605558562484.us-central1.run.app";

let map;
let markers = [];
let nextPageToken = null;
let allPlaces = [];
let activeInfoWindow = null;

// ==============================
// INICIAR MAPA
// ==============================
function initMap() {
    map = new google.maps.Map(document.getElementById("map"), {
        center: { lat: 4.7110, lng: -74.0721 },
        zoom: 12,
        styles: [{ featureType: "poi.business", elementType: "labels", stylers: [{ visibility: "off" }] }]
    });
}

// ==============================
// LIMPIAR MARCADORES
// ==============================
function clearMarkers() {
    markers.forEach(m => m.setMap(null));
    markers = [];
    if (activeInfoWindow) { activeInfoWindow.close(); activeInfoWindow = null; }
}

// ==============================
// RENDERIZAR RESULTADOS
// ==============================
function renderPlaces() {
    const container = document.getElementById("results");
    container.innerHTML = "";

    const bounds = new google.maps.LatLngBounds();
    let hasMarkers = false;

    clearMarkers();

    allPlaces.forEach((place, index) => {
        const name    = place.name || "Sin nombre";
        const website = place.website || "Sin sitio web";

        const rawEmails = place.emails || [];
        const cleanEmails = [...new Set(
            rawEmails
                .map(e => { const m = e.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/); return m ? m[0] : ""; })
                .filter(e => e !== "")
        )];
        const emailsHtml = cleanEmails.length
            ? cleanEmails.map(e => `<span class="email-highlight">${e}</span>`).join("<br>")
            : `<span class="loading-emails" id="email-${index}">⏳ Buscando emails...</span>`;

        const card = document.createElement("div");
        card.className = "place-card";
        card.id = `card-${index}`;
        card.innerHTML = `
            <h3><span class="place-number">${index + 1}</span> ${name}</h3>
            <p><strong>Sitio Web:</strong><br>
                ${website !== "Sin sitio web"
                    ? `<a href="${website}" target="_blank">${website}</a>`
                    : "Sin sitio web"}
            </p>
            <p><strong>Emails Encontrados:</strong><br>${emailsHtml}</p>
        `;
        container.appendChild(card);

        const lat = place.lat;
        const lng = place.lng;

        if (lat && lng) {
            const pos = { lat: parseFloat(lat), lng: parseFloat(lng) };

            const marker = new google.maps.Marker({
                position: pos,
                map: map,
                title: name,
                label: { text: (index + 1).toString(), color: "white", fontWeight: "bold" },
                animation: google.maps.Animation.DROP
            });

            const infoWindow = new google.maps.InfoWindow({
                content: `
                    <div style="max-width:220px;font-family:sans-serif;">
                        <strong>${name}</strong><br>
                        ${website !== "Sin sitio web"
                            ? `<a href="${website}" target="_blank" style="color:#1a73e8;font-size:12px;">${website}</a>`
                            : '<span style="color:#999;font-size:12px;">Sin sitio web</span>'}
                    </div>`
            });

            card.addEventListener("click", () => {
                map.setZoom(16); map.panTo(pos);
                if (activeInfoWindow) activeInfoWindow.close();
                infoWindow.open(map, marker);
                activeInfoWindow = infoWindow;
                document.querySelectorAll(".place-card").forEach(c => c.classList.remove("active"));
                card.classList.add("active");
            });

            marker.addListener("click", () => {
                map.setZoom(16); map.panTo(pos);
                if (activeInfoWindow) activeInfoWindow.close();
                infoWindow.open(map, marker);
                activeInfoWindow = infoWindow;
                document.querySelectorAll(".place-card").forEach(c => c.classList.remove("active"));
                card.classList.add("active");
                card.scrollIntoView({ behavior: "smooth", block: "center" });
            });

            markers.push(marker);
            bounds.extend(pos);
            hasMarkers = true;
        }
    });

    if (hasMarkers && map) map.fitBounds(bounds);
    updateLoadMoreBtn();
}

// ==============================
// ENRIQUECER CON EMAILS (2do paso)
// ==============================
async function enrichPlaces(places, startIndex) {
    try {
        const response = await fetch(`${BACKEND}/enrich`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ places })
        });
        const data = await response.json();
        const enriched = data.places || [];

        enriched.forEach((place, i) => {
            const globalIndex = startIndex + i;
            allPlaces[globalIndex] = { ...allPlaces[globalIndex], ...place };

            // Actualizar emails en la tarjeta ya renderizada
            const emailSpan = document.getElementById(`email-${globalIndex}`);
            if (emailSpan) {
                const rawEmails = place.emails || [];
                const cleanEmails = [...new Set(
                    rawEmails
                        .map(e => { const m = e.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/); return m ? m[0] : ""; })
                        .filter(e => e !== "")
                )];
                emailSpan.outerHTML = cleanEmails.length
                    ? cleanEmails.map(e => `<span class="email-highlight">${e}</span>`).join("<br>")
                    : "Sin emails";
            }

            // Actualizar website en la tarjeta si llegó vacío antes
            if (place.website && place.website !== "Sin sitio web") {
                const card = document.getElementById(`card-${globalIndex}`);
                if (card) {
                    const webP = card.querySelector("p:nth-child(2)");
                    if (webP && webP.textContent.includes("Sin sitio web")) {
                        webP.innerHTML = `<strong>Sitio Web:</strong><br><a href="${place.website}" target="_blank">${place.website}</a>`;
                    }
                }
            }
        });

    } catch (e) {
        console.error("[enrichPlaces] Error:", e);
    }
}

// ==============================
// BUSCAR
// ==============================
async function searchPlaces(loadMore = false) {
    const queryInput    = document.getElementById("queryInput");
    const locationInput = document.getElementById("locationInput");
    if (!queryInput || !locationInput) return;

    const query    = queryInput.value.trim();
    const location = locationInput.value.trim();

    if (!query || !location) {
        alert("Por favor, escribe qué buscas y dónde.");
        return;
    }

    const fullQuery = `${query} en ${location}`;

    try {
        if (!loadMore) {
            document.getElementById("results").innerHTML = `<p>Buscando...</p>`;
            clearMarkers();
            allPlaces = [];
            nextPageToken = null;
        }

        let url = `${BACKEND}/search?query=${encodeURIComponent(fullQuery)}`;
        if (loadMore && nextPageToken) url += `&page_token=${encodeURIComponent(nextPageToken)}`;

        const response = await fetch(url);
        const data     = await response.json();
        const places   = data.places?.results || [];

        nextPageToken = data.places?.next_page_token || null;

        const startIndex = allPlaces.length;
        allPlaces = [...allPlaces, ...places];

        renderPlaces();

        // Enriquecer con emails en segundo plano
        if (places.length > 0) {
            enrichPlaces(places, startIndex);
        }

    } catch (error) {
        console.error(error);
        document.getElementById("results").innerHTML = `<p>Error al conectar con el servidor.</p>`;
    }
}

// ==============================
// CARGAR MÁS
// ==============================
function loadMorePlaces() {
    console.log("loadMorePlaces llamado, token:", nextPageToken);
    if (nextPageToken) searchPlaces(true);
}

function updateLoadMoreBtn() {
    const btn = document.getElementById("loadMoreBtn");
    if (!btn) return;
    btn.classList.toggle("hidden-btn", !nextPageToken);
}

// ==============================
// EXPORTAR CSV
// ==============================
function downloadCSV() {
    if (allPlaces.length === 0) return alert("No hay resultados");

    let csv = "Nombre,Sitio Web,Emails\n";
    allPlaces.forEach(place => {
        const name    = (place.name || "Sin nombre").replace(/"/g, '""');
        const website = (place.website || "Sin sitio web").replace(/"/g, '""');
        const raw     = place.emails || [];
        const clean   = [...new Set(raw.map(e => {
            const m = e.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
            return m ? m[0] : "";
        }).filter(e => e !== ""))];
        const emails  = (clean.length ? clean.join(" | ") : "Sin emails").replace(/"/g, '""');
        csv += `"${name}","${website}","${emails}"\n`;
    });

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const a    = document.createElement("a");
    a.href     = window.URL.createObjectURL(blob);
    a.download = "leads.csv";
    a.click();
}

document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("queryInput");
    if (input) input.addEventListener("keypress", e => { if (e.key === "Enter") searchPlaces(); });
});

