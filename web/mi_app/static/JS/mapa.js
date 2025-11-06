// Espera a que el contenido de la página esté completamente cargado
document.addEventListener("DOMContentLoaded", () => {
    const boton = document.getElementById("mostrarMapa");
    const mapaDiv = document.getElementById("map");

    // Cuando se hace clic en el botón
    boton.addEventListener("click", () => {
       
        // Si el mapa está oculto, se muestra
        if (mapaDiv.style.display === "none") {
            mapaDiv.style.display = "block";
            boton.textContent = "Ocultar mapa"; 

            // Si el mapa aún no se ha cargado
            if (!mapaDiv.dataset.loaded) {
                
                // Se crea el mapa centrado en Donostia-San Sebastián con las coordenadas dadas.
                const map = L.map('map').setView([43.3199738, -1.9723845], 15);

                // Capa base del mapa
                L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 19,
                    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                }).addTo(map);

                // Marcador con popup informativo
                L.marker([43.3199738, -1.9723845]).addTo(map)
                    .bindPopup(`
                        <b>DONOSWAVE</b><br>
                        Nazaret Zentroa<br>
                        Donostia-San Sebastián<br>
                        <a href="https://maps.app.goo.gl/iR4Lowr8q8D9dkv7A" target="_blank">Ver en Google Maps</a>
                    `)
                    .openPopup();

                // Marca el mapa como cargado para no volver a crearlo
                mapaDiv.dataset.loaded = "true"; 
            }
        } 
        // Si el mapa está visible, se oculta
        else {
            mapaDiv.style.display = "none";
            boton.textContent = "Ver mapa"; 
        }
    });
});
