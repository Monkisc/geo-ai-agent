let map;
let markers = [];
let nextPageToken = null;

function initMap() {

    map = new google.maps.Map(document.getElementById("map"), {

        center: { lat: 4.7110, lng: -74.0721 },

        zoom: 10,

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
// BUSCAR
// ===============================
async function searchPlaces(loadMore = false) {

    const query = document
        .getElementById("searchInput")
        .value
        .trim();

    if (!query) {

        alert("Escribe una búsqueda");

        return;

    }

    const resultsContainer =
        document.getElementById("results");

    try {

        if (!loadMore) {

            resultsContainer.innerHTML =
                "<p>Buscando lugares...</p>";

            clearMarkers();

        }

        let url =
            `https://geo-ai-agent.onrender.com/search?query=${encodeURIComponent(query)}`;

        // PAGINACIÓN
        if (loadMore && nextPageToken) {

            url += `&page_token=${nextPageToken}`;

        }

        const response = await fetch(url);

        if (!response.ok) {

            throw new Error("Error del servidor");

        }

        const data = await response.json();

        console.log("RESPUESTA:", data);

        const places = data.places.results || [];

        console.log("PLACES:", places);

        nextPageToken =
            data.places.next_page_token || null;

        if (!loadMore) {

            resultsContainer.innerHTML = "";

        }

        if (places.length === 0 && !loadMore) {

            resultsContainer.innerHTML =
                "<p>No se encontraron resultados.</p>";

            return;

        }

        const bounds = new google.maps.LatLngBounds();

        places.forEach(place => {

            const name =
                place.name || "Sin nombre";

            const address =
                place.address || "Sin dirección";

            const lat =
                place.location?.lat;

            const lng =
                place.location?.lng;

            // ===============================
            // CARD
            // ===============================
            const card =
                document.createElement("div");

            card.className = "place-card";

            card.innerHTML = `
                <h3>${name}</h3>

                <p>
                    <strong>Dirección:</strong><br>
                    ${address}
                </p>
            `;

            resultsContainer.appendChild(card);

            // ===============================
            // MAPA
            // ===============================
            if (lat && lng) {

                const marker =
                    new google.maps.Marker({

                        position: { lat, lng },

                        map,

                        title: name,

                    });

                const infoWindow =
                    new google.maps.InfoWindow({

                        content: `
                            <div style="max-width:200px;">
                                <h3>${name}</h3>
                                <p>${address}</p>
                            </div>
                        `

                    });

                // CLICK MARKER
                marker.addListener("click", () => {

                    infoWindow.open(map, marker);

                    map.setCenter({ lat, lng });

                    map.setZoom(15);

                });

                // CLICK CARD
                card.addEventListener("click", () => {

                    map.setCenter({ lat, lng });

                    map.setZoom(15);

                    infoWindow.open(map, marker);

                });

                markers.push(marker);

                bounds.extend({ lat, lng });

            }

        });

        // AUTO ZOOM
        if (places.length > 0) {

            map.fitBounds(bounds);

        }

        // ===============================
        // IA
        // ===============================
        if (!loadMore && data.analysis) {

            const analysisDiv =
                document.getElementById("analysis");

            if (analysisDiv) {

                analysisDiv.innerHTML = `
                    <h2>Análisis IA</h2>
                    <p>${data.analysis}</p>
                `;

            }

        }

        // ===============================
        // BOTÓN CARGAR MÁS
        // ===============================
        const loadMoreBtn =
            document.getElementById("loadMoreBtn");

        if (nextPageToken) {

            loadMoreBtn.style.display = "block";

        } else {

            loadMoreBtn.style.display = "none";

        }

    } catch (error) {

        console.error(error);

        resultsContainer.innerHTML =
            "<p>Error al buscar resultados.</p>";

    }

}

// ===============================
// CARGAR MÁS
// ===============================
function loadMorePlaces() {

    searchPlaces(true);

}

// ===============================
// CSV
// ===============================
function downloadCSV() {

    const cards =
        document.querySelectorAll(".place-card");

    if (cards.length === 0) {

        alert("No hay resultados");

        return;

    }

    let csv =
        "Nombre,Direccion\n";

    cards.forEach(card => {

        const lines =
            card.innerText.split("\n");

        const nombre =
            lines[0] || "";

        const direccion =
            lines[2] || "";

        csv +=
            `"${nombre}","${direccion}"\n`;

    });

    const blob =
        new Blob([csv], {
            type: "text/csv"
        });

    const url =
        window.URL.createObjectURL(blob);

    const a =
        document.createElement("a");

    a.href = url;

    a.download = "resultados.csv";

    a.click();

    window.URL.revokeObjectURL(url);

}

// ===============================
// ENTER
// ===============================
document.addEventListener("DOMContentLoaded", () => {

    const input =
        document.getElementById("searchInput");

    if (input) {

        input.addEventListener("keypress", (e) => {

            if (e.key === "Enter") {

                searchPlaces();

            }

        });

    }

});
