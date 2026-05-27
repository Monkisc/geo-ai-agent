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
        zoom: 12, // Subí un poco el zoom inicial para que Bogotá se aprecie mejor desde el arranque
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

    // Caja virtual (bounds) para encuadrar automáticamente el mapa según los resultados encontrados
    const bounds = new google.maps.LatLngBounds();
    let hasMarkers = false;

    visiblePlaces.forEach(place => {
        const name = place.name || "Sin nombre";
        const address = place.address || "Sin dirección";
        const phone = place.phone || "Sin teléfono";
        const website = place.website || "Sin sitio web";
        const emails = place.emails?.length
            ? place.emails.join(", ")
            : "Sin emails";

        // EXTRACCIÓN CORREGIDA: Acceso directo a la raíz del objeto enviado por tu Python
        const lat = place.lat;
        const lng = place.lng;

        // ===============================
        // CARD (HTML de la barra lateral)
        // ===============================
        const card = document.createElement("div");
        card.className = "place-card";
        card.innerHTML = `
            <h3>${name}</h3>
            <p><strong>Dirección:</strong><br>${address}</p>
            <p><strong>Teléfono:</strong><br>${phone}</p>
            <p>
                <strong>Sitio Web:</strong><br>
                <a href="${website}" target="_blank">
                    ${website}
                </a>
            </p>
            <p><strong>Emails:</strong><br>${emails}</p>
        `;

        // EVENTO CLICK EN LA TARJETA: Mueve la cámara del mapa directo al lugar seleccionado
        card.addEventListener("click", () => {
            if (lat && lng) {
                map.setCenter({ lat: parseFloat(lat), lng: parseFloat(lng) });
                map.setZoom(16); // Zoom cercano para detallar la zona del colegio
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
                animation: google.maps.Animation.DROP // Efecto de caída para cada marcador
            });

            // Ventana informativa emergente al hacer clic en el pin del mapa
            const infowindow = new google.maps.InfoWindow({
                content: `<strong>${name}</strong><br>${address}`
            });

            marker.addListener("click", () => {
                infowindow.open(map, marker);
            });

            markers.push(marker);
            bounds.extend(markerPosition); // Expandir el contenedor virtual para incluir la coordenada
            hasMarkers = true;
        }
    });

    // Si hay marcadores válidos en el mapa, ajusta el encuadre automáticamente
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
                <p>Buscando lugares...</p>
            `;
            clearMarkers();
            allPlaces = [];
            currentPage = 1;
        }

        // ===============================
        // URL BACKEND (Render)
        // ===============================
        let url = `https://geo-ai-agent.onrender.com/search?query=${encodeURIComponent(query)}`;

        if (loadMore && nextPageToken) {
            url += `&page_token=${nextPageToken}`;
        }

        // ===============================
        // FETCH
        // ===============================
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }

        const data = await response.json();
        console.log("RESPUESTA:", data);

        // ===============================
        // PLACES
        // ===============================
        const places = data.places.results || [];
        console.log("PLACES:", places);

        nextPageToken = data.places.next_page_token || null;

        // Guardar resultados acumulados
        allPlaces = [...allPlaces, ...places];

        // Renderizar todo en la barra lateral y en el mapa
        renderPlaces();

        // ===============================
        // ANÁLISIS IA
        // ===============================
        if (!loadMore && data.analysis) {
            const analysisDiv = document.getElementById("analysis");
            if (analysisDiv) {
                analysisDiv.innerHTML = `
                    <h2>Análisis IA</h2>
                    <p>${data.analysis}</p>
                `;
            }
        }

    } catch (error) {
        console.error(error);
        const resultsContainer = document.getElementById("results");
        resultsContainer.innerHTML = `
            <p>Error al buscar resultados.</p>
        `;
    }
}

// ===============================
// CARGAR MÁS
// ===============================
async function loadMorePlaces() {
    const visible = currentPage * placesPerPage;

    // Si todavía hay resultados ocultos de forma local
    if (visible < allPlaces.length) {
        currentPage++;
        renderPlaces();
        return;
    }

    // Si ya no hay locales pero Google tiene un token para más páginas
    if (nextPageToken) {
        await searchPlaces(true);
        currentPage++;
        renderPlaces();
    }
}

// ===============================
// EXPORTAR CSV
// ===============================
function downloadCSV() {
    const cards = document.querySelectorAll(".place-card");

    if (cards.length === 0) {
        alert("No hay resultados para descargar");
        return;
    }

    let csv = "Nombre,Direccion,Telefono,Website,Emails\n";

    cards.forEach(card => {
        const lines = card.innerText.split("\n");
        const nombre = lines[0] || "";
        const direccion = lines[2] || "";
        const telefono = lines[4] || "";
        const website = lines[6] || "";
        const emails = lines[8] || "";

        csv += `"${nombre}","${direccion}","${telefono}","${website}","${emails}"\n`;
    });

    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "resultados.csv";
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
