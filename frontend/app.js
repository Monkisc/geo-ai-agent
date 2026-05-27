let map;
let markers = [];
let lastPlaces = [];

function initMap() {

    map = new google.maps.Map(document.getElementById("map"), {

        center: {
            lat: 4.7110,
            lng: -74.0721
        },

        zoom: 11
    });
}

async function searchPlaces() {

    const input = document.getElementById("searchInput");

    if (!input) {
        alert("No existe el input searchInput");
        return;
    }

    const query = input.value;

    if (!query) {

        alert("Escribe una búsqueda");
        return;
    }

    const resultsDiv = document.getElementById("results");

    resultsDiv.innerHTML = `
        <div class="loading">
            Buscando lugares...
        </div>
    `;

    try {

        const response = await fetch(
            `http://127.0.0.1:8000/search?query=${encodeURIComponent(query)}`
        );

        const data = await response.json();

        console.log("RESPUESTA:", data);

        // LIMPIAR MAPA
        markers.forEach(marker => marker.setMap(null));

        markers = [];

        resultsDiv.innerHTML = "";

        // OBTENER RESULTS
        let places = [];

        if (data.places && data.places.results) {

            places = data.places.results;

        } else if (data.results) {

            places = data.results;
        }

        console.log("PLACES:", places);

        // GUARDAR PARA DESCARGA
        lastPlaces = places;

        if (!places.length) {

            resultsDiv.innerHTML = `
                <div class="no-results">
                    No se encontraron resultados
                </div>
            `;

            return;
        }

        const bounds = new google.maps.LatLngBounds();

        places.forEach(place => {

            if (
                place.lat === undefined ||
                place.lng === undefined
            ) {
                return;
            }

            // MAPA
            const marker = new google.maps.Marker({

                position: {
                    lat: place.lat,
                    lng: place.lng
                },

                map: map,

                title: place.name
            });

            markers.push(marker);

            bounds.extend({
                lat: place.lat,
                lng: place.lng
            });

            // EMAILS
            let emailsHTML = "";

            if (place.emails && place.emails.length > 0) {

                emailsHTML = `
                    <div class="emails">
                        <strong>✉️ Correos:</strong><br>
                        ${place.emails.join("<br>")}
                    </div>
                `;
            }

            // TELÉFONOS
            let phonesHTML = "";

            if (place.phones && place.phones.length > 0) {

                phonesHTML = `
                    <div class="phones">
                        <strong>📞 Teléfonos:</strong><br>
                        ${place.phones.join("<br>")}
                    </div>
                `;
            }

            // WEBSITE
            let websiteHTML = "";

            if (place.website) {

                websiteHTML = `
                    <p>
                        🌐
                        <a href="${place.website}" target="_blank">
                            Sitio Web
                        </a>
                    </p>
                `;
            }

            // CARD
            const card = document.createElement("div");

            card.className = "place-card";

            card.innerHTML = `

                <h3>${place.name || "Sin nombre"}</h3>

                ${place.rating ? `
                    <p>⭐ ${place.rating}</p>
                ` : ""}

                ${place.address ? `
                    <p>📍 ${place.address}</p>
                ` : ""}

                ${websiteHTML}

                ${phonesHTML}

                ${emailsHTML}

            `;

            card.addEventListener("click", () => {

                map.panTo({
                    lat: place.lat,
                    lng: place.lng
                });

                map.setZoom(16);
            });

            resultsDiv.appendChild(card);
        });

        map.fitBounds(bounds);

    } catch (error) {

        console.error(error);

        resultsDiv.innerHTML = `
            <div class="error">
                Error conectando con backend
            </div>
        `;
    }
}


// DESCARGAR CSV
function downloadCSV() {

    if (!lastPlaces.length) {

        alert("No hay datos para descargar");
        return;
    }

    let csv = "Nombre,Direccion,Website,Telefonos,Emails,Rating\n";

    lastPlaces.forEach(place => {

        const row = [

            `"${place.name || ""}"`,
            `"${place.address || ""}"`,
            `"${place.website || ""}"`,
            `"${(place.phones || []).join(" | ")}"`,
            `"${(place.emails || []).join(" | ")}"`,
            `"${place.rating || ""}"`

        ].join(",");

        csv += row + "\n";
    });

    const blob = new Blob([csv], {
        type: "text/csv;charset=utf-8;"
    });

    const link = document.createElement("a");

    const url = URL.createObjectURL(blob);

    link.setAttribute("href", url);

    link.setAttribute("download", "resultados.csv");

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);
}


// ENTER
document.addEventListener("DOMContentLoaded", () => {

    const input = document.getElementById("searchInput");

    if (input) {

        input.addEventListener("keypress", function (e) {

            if (e.key === "Enter") {

                searchPlaces();
            }
        });
    }
});

