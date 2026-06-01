let map;
let markers = [];
let nextPageToken = null;
let allPlaces = [];
let currentPage = 1;

const placesPerPage = 25; 

// INICIAR MAPA EN COORDENADAS POR DEFECTO
function initMap() {
    map = new google.maps.Map(document.getElementById("map"), {
        center: { lat: 4.7110, lng: -74.0721 },
        zoom: 12,
        styles: [
            {
                featureType: "poi.business",
                elementType: "labels",
                stylers: [{ visibility: "off" }]
            }
        ]
    });
}

// LIMPIAR MARCADORES ANTERIORES
function clearMarkers() {
    markers.forEach(marker => marker.setMap(null));
    markers = [];
}

// RENDERIZAR TARJETAS Y COORDENADAS EN EL MAPA
function renderPlaces() {
    const resultsContainer = document.getElementById("results");
    resultsContainer.innerHTML = "";

    const end = currentPage * placesPerPage;
    const visiblePlaces = allPlaces.slice(0, end);

    const bounds = new google.maps.LatLngBounds();
    let hasMarkers = false;

    clearMarkers();

    visiblePlaces.forEach((place, index) => {
        const name = place.name || "Sin nombre";
        const website = place.website || "Sin sitio web";
        const errorsOrEmails = place.emails?.length ? place.emails.join(", ") : "Sin emails";
        
        // CORRECCIÓN CLAVE: Extraemos lat/lng tolerando variaciones del backend (Geometry u objeto plano)
        let lat = place.lat || place.geometry?.location?.lat;
        let lng = place.lng || place.geometry?.location?.lng;

        const cardId = `card-${index}`;

        const card = document.createElement("div");
        card.className = "place-card";
        card.id = cardId;
        card.innerHTML = `
            <h3>${name}</h3>
            <p><strong>Sitio Web:</strong><br><a href="${website}" target="_blank">${website}</a></p>
            <p><strong>Emails Reales Encontrados:</strong><br><span class="email-highlight">${errorsOrEmails}</span></p>
        `;

        resultsContainer.appendChild(card);

        // Validar que las coordenadas existan y sean números correctos
        if (lat !== undefined && lng !== undefined) {
            const parsedLat = parseFloat(lat);
            const parsedLng = parseFloat(lng);

            if (!isNaN(parsedLat) && !isNaN(parsedLng)) {
                const markerPosition = { lat: parsedLat, lng: parsedLng };

                const marker = new google.maps.Marker({
                    position: markerPosition,
                    map: map,
                    title: name,
                    label: (index + 1).toString(),
                    animation: google.maps.Animation.DROP
                });

                const infowindow = new google.maps.InfoWindow({
                    content: `<div style="color: #333; padding: 4px; font-family: sans-serif;"><strong style="font-size: 13px;">${name}</strong></div>`
                });

                marker.addListener("click", () => {
                    infowindow.open(map, marker);
                    document.querySelectorAll(".place-card").forEach(c => c.classList.remove("active-card"));
                    const targetCard = document.getElementById(cardId);
                    if (targetCard) {
                        targetCard.classList.add("active-card");
                        targetCard.scrollIntoView({ behavior: "smooth", block: "center" });
                    }
                });

                card.addEventListener("click", () => {
                    document.querySelectorAll(".place-card").forEach(c => c.classList.remove("active-card"));
                    card.classList.add("active-card");
                    map.setCenter(markerPosition);
                    map.setZoom(16);
                    infowindow.open(map, marker);
                });

                markers.push(marker);
                bounds.extend(markerPosition);
                hasMarkers = true;
            }
        }
    });

    // Ajustar la cámara para que encuadre todos los pines automáticamente
    if (hasMarkers && map) {
        map.fitBounds(bounds);
    }

    const loadMoreBtn = document.getElementById("loadMoreBtn");
    if (loadMoreBtn) {
        if (end < allPlaces.length || nextPageToken) {
            loadMoreBtn.style.display = "block";
        } else {
            loadMoreBtn.style.display = "none";
        }
    }
}

// SOLICITUD AL BACKEND EN CLOUD RUN
async function searchPlaces(loadMore = false) {
    const queryInput = document.getElementById("searchInput");
    if (!queryInput) return;

    const query = queryInput.value.trim();
    if (!query) {
        alert("Escribe una búsqueda");
        return;
    }

    try {
        const resultsContainer = document.getElementById("results");

        if (!loadMore) {
            resultsContainer.innerHTML = `<p>Buscando lugares y escaneando correos reales...</p>`;
            clearMarkers();
            allPlaces = [];
            currentPage = 1;
        }

        let url = `https://geo-ai-agent-605558562484.us-central1.run.app/search?query=${encodeURIComponent(query)}`;

        if (loadMore && nextPageToken) {
            url += `&page_token=${nextPageToken}`;
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);

        const data = await response.json();
        
        // Mapeo flexible de la respuesta del backend
        const places = data.places?.results || data.places || [];

        nextPageToken = data.places?.next_page_token || null;
        allPlaces = [...allPlaces, ...places];

        renderPlaces();

        if (!loadMore && data.analysis) {
            const analysisDiv = document.getElementById("analysis");
            if (analysisDiv) {
                analysisDiv.innerHTML = `
                    <h2>Análisis de Prospección IA</h2>
                    <p>${data.analysis}</p>
                `;
            }
        }

    } catch (error) {
        console.error(error);
        document.getElementById("results").innerHTML = `<p>Error al conectar con el servidor.</p>`;
    }
}

async function loadMorePlaces() {
    const visible = currentPage * placesPerPage;
    if (visible < allPlaces.length) {
        currentPage++;
        renderPlaces();
        return;
    }
    if (nextPageToken) {
        await searchPlaces(true);
        currentPage++;
        renderPlaces();
    }
}

function downloadCSV() {
    if (allPlaces.length === 0) {
        alert("No hay resultados para descargar");
        return;
    }
    let csv = "Nombre de la Empresa/Colegio,Sitio Web,Emails Encontrados\n";
    allPlaces.forEach(place => {
        const name = (place.name || "Sin nombre").replace(/"/g, '""');
        const website = (place.website || "Sin sitio web").replace(/"/g, '""');
        const emails = (place.emails?.length ? place.emails.join(" | ") : "Sin emails").replace(/"/g, '""');
        csv += `"${name}","${website}","${emails}"\n`;
    });
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "leads_digitales.csv";
    a.click();
    window.URL.revokeObjectURL(url);
}

document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("searchInput");
    if (input) {
        input.addEventListener("keypress", (e) => {
            if (e.key === "Enter") searchPlaces();
        });
    }
});
