
// Pobieranie klucza z .env (FastAPI nie odczyta .env w JS, więc trzeba wrzucić do JS przez backend lub inline)
// Na razie wstaw wprost:
const API_KEY = "25ae8c36b22398f35b25584807571f27";
const API_URL = "https://api.openweathermap.org/data/2.5/weather?q=";

// Nakładki mapy
let baseLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png");
let tempLayer = L.tileLayer(`https://tile.openweathermap.org/map/temp_new/{z}/{x}/{y}.png?appid=${API_KEY}`, {opacity:1.0});
let rainLayer = L.tileLayer(`https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid=${API_KEY}`, {opacity:1.0});
let cloudsLayer = L.tileLayer(`https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png?appid=${API_KEY}`, {opacity:1.0});
let windLayer = L.tileLayer(`https://tile.openweathermap.org/map/wind_new/{z}/{x}/{y}.png?appid=${API_KEY}`, {opacity:1.0});

let map = L.map("map", { center:[52.0,19.0], zoom:6, layers:[baseLayer,tempLayer] });

const layers = { temp: tempLayer, rain: rainLayer, clouds: cloudsLayer, wind: windLayer };

const legends = {
  temp:`<b>Temperatura (°C)</b>
        <div class="legend-container">
          <div class="legend-bar legend-temp-bar"></div>
          <div class="legend-labels"><span>-20</span><span>0</span><span>20</span><span>40+</span></div>
        </div>`,
  rain:`<b>Opady (mm/h)</b>
        <div class="legend-container">
          <div class="legend-bar legend-rain-bar"></div>
          <div class="legend-labels"><span>0</span><span>2</span><span>5</span><span>10+</span></div>
        </div>`,
  clouds:`<b>Zachmurzenie (%)</b>
        <div class="legend-container">
          <div class="legend-bar legend-clouds-bar"></div>
          <div class="legend-labels"><span>0%</span><span>25%</span><span>50%</span><span>100%</span></div>
        </div>`,
  wind:`<b>Wiatr (m/s)</b>
        <div class="legend-container">
          <div class="legend-bar legend-wind-bar"></div>
          <div class="legend-labels"><span>0</span><span>5</span><span>10</span><span>20+</span></div>
        </div>`
};


function switchLayer(name){
  Object.values(layers).forEach(l=>map.removeLayer(l));
  map.addLayer(layers[name]);
  document.getElementById("legendContainer").innerHTML = legends[name];
}

document.querySelectorAll('input[name="weatherLayer"]').forEach(radio=>{
  radio.addEventListener('change', e=>switchLayer(e.target.value));
});

// domyślnie temperatura
switchLayer("temp");

document.getElementById("searchBtn").addEventListener("click", async ()=>{
  const city = document.getElementById("cityInput").value;
  if(!city) return alert("Wpisz miasto!");
  try{
    const res = await fetch(`${API_URL}${city}&appid=${API_KEY}&units=metric&lang=pl`);
    const data = await res.json();
    if(data.cod!==200){ document.getElementById("weatherInfo").innerText="Nie znaleziono miasta!"; return; }

    const {coord, main, weather, wind, name} = data;
    document.getElementById("weatherInfo").innerHTML=`
      <h2>${name}</h2>
      <p>${weather[0].description}</p>
      <p>Temperatura: ${main.temp} °C</p>
      <p>Wilgotność: ${main.humidity} %</p>
      <p>Ciśnienie: ${main.pressure} hPa</p>
      <p>Wiatr: ${wind.speed} m/s</p>
    `;

    map.setView([coord.lat, coord.lon],10);
    L.marker([coord.lat,coord.lon]).addTo(map)
      .bindPopup(`${name}: ${main.temp}°C, ${weather[0].description}`)
      .openPopup();

  }catch(err){ console.error(err); alert("Błąd pobierania danych pogodowych!"); }
});
