let map;
let markers = [];
let nextPageToken = null;

let allPlaces = [];
let currentPage = 1;

const placesPerPage = 5;

// ===============================
// INICIAR MAPA
// ===============================
function initMap() {
    map = new google.maps.Map(document.getElementById("map"), {
        center: { lat: 4.7110, lng: -74.0721 },
        zoom: 12, // Bogotá desde el arranque
    });
}

// ===============================
// LIMPIAR MARCADORES
// ===============================
function clearMarkers() {
    markers.forEach(marker => marker.setMap(null));
    markers = [];
}

// ===============================
// RENDERIZAR RESULTADOS
// ===============================
function renderPlaces() {
    const resultsContainer = document.getElementById("results");
    resultsContainer.innerHTML = "";

    const end = currentPage * placesPerPage;
    const visiblePlaces = allPlaces.slice(0, end);

    const bounds = new google.maps.LatLngBounds();
    let hasMarkers = false;

    visiblePlaces.forEach(place => {
        const name = place.name || "Sin nombre";
        const website = place.website || "Sin sitio web";
        const errorsOrEmails = place.emails?.length
            ? place.emails.join(", ")
            : "Sin emails";

        const lat = place.lat;
        const lng = place.lng;

        // ===============================
        // CARD OPTIMIZADA (Solo Sitio Web y Emails)
        // ===============================
        const card = document.createElement("div");
        card.className = "place-card";
        card.innerHTML = `
            <h3>${name}</h3>
            <p>
                <strong>Sitio Web:</strong><br>
                <a href="${website}" target="_blank">
                    ${website}
                </a>
            </p>
            <p><strong>Emails Reales Encontrados:</strong><br>${errorsOrEmails}</p>
        `;

        // EVENTO CLICK EN LA TARJETA
        card.addEventListener("click", () => {
            if (lat && lng) {
                map.setCenter({ lat: parseFloat(lat), lng: parseFloat(lng) });
                map.setZoom(16);
            }
        });

        resultsContainer.appendChild(card);

        // ===============================
        // MAPA (Pintar pines dinámicos)
        // ===============================
        if (lat && lng) {
            const markerPosition = { lat: parseFloat(lat), lng: parseFloat(lng) };

            const marker = new google.maps.Marker({
                position: markerPosition,
                map: map,
                title: name,
                animation: google.maps.Animation.DROP
            });

            const infowindow = new google.maps.InfoWindow({
                content: `<strong>${name}</strong><br><a href="${website}" target="_blank">${website}</a>`
            });

            marker.addListener("click", () => {
                infowindow.open(map, marker);
            });

            markers.push(marker);
            bounds.extend(markerPosition);
            hasMarkers = true;
        }
    });

    if (hasMarkers) {
        map.fitBounds(bounds);
    }

    // ===============================
    // BOTÓN CARGAR MÁS
    // ===============================
    const loadMoreBtn = document.getElementById("loadMoreBtn");
    if (end < allPlaces.length || nextPageToken) {
        loadMoreBtn.style.display = "block";
    } else {
        loadMoreBtn.style.display = "none";
    }
}

// ===============================
// BUSCAR LUGARES
// ===============================
async function searchPlaces(loadMore = false) {
    const queryInput = document.getElementById("searchInput");

    if (!queryInput) {
        console.error("No existe el input #searchInput");
        return;
    }

    const query = queryInput.value.trim();

    if (!query) {
        alert("Escribe una búsqueda");
        return;
    }

    try {
        const resultsContainer = document.getElementById("results");

        if (!loadMore) {
            resultsContainer.innerHTML = `
                <p>Buscando lugares y escaneando correos reales...</p>
            `;
            clearMarkers();
            allPlaces = [];
            currentPage = 1;
        }

        // URL apuntando a tu backend de Google Cloud Run
        let url = `https://geo-ai-agent-605558562484.us-central1.run.app/search?query=${encodeURIComponent(query)}`;

        if (loadMore && nextPageToken) {
            url += `&page_token=${nextPageToken}`;
        }

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }

        const data = await response.json();
        console.log("RESPUESTA:", data);

        const places = data.places.results || [];
        console.log("PLACES:", places);

        nextPageToken = data.places.next_page_token || null;
        allPlaces = [...allPlaces, ...places];

        renderPlaces();

        // ===============================
        // ANÁLISIS IA
        // ===============================
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
        const resultsContainer = document.getElementById("results");
        resultsContainer.innerHTML = `
            <p>Error al buscar resultados y raspar sitios web.</p>
        `;
    }
}

// ===============================
// CARGAR MÁS
// ===============================
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

// ===============================
// EXPORTAR CSV OPTIMIZADO
// ===============================
function downloadCSV() {
    if (allPlaces.length === 0) {
        alert("No hay resultados para descargar");
        return;
    }

    // Encabezado limpio enfocado en Leads
    let csv = "Nombre de la Empresa/Colegio,Sitio Web,Emails Encontrados\n";

    allPlaces.forEach(place => {
        const name = place.name || "Sin nombre";
        const website = place.website || "Sin sitio web";
        const emails = place.emails?.length ? place.emails.join(" | ") : "Sin emails";

        // Reemplazar comillas dobles para evitar que se rompa el formato del archivo CSV
        const cleanName = name.replace(/"/g, '""');
        const cleanWebsite = website.replace(/"/g, '""');
        const cleanEmails = emails.replace(/"/g, '""');

        csv += `"${cleanName}","${cleanWebsite}","${cleanEmails}"\n`;
    });

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "leads_digitales.csv";
    a.click();
    window.URL.revokeObjectURL(url);
}

// ===============================
// ENTER PARA BUSCAR
// ===============================
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("searchInput");
    if (input) {
        input.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                searchPlaces();
            }
        });
    }
});
