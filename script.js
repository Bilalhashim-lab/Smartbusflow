// Map initialization for track page
document.addEventListener('DOMContentLoaded', function () {
  const mapEl = document.getElementById('map');
  if (mapEl) {
    const map = L.map('map').setView([28.7041,77.1025], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap'
    }).addTo(map);

    // place markers from list
    const busItems = document.querySelectorAll('.bus-list li');
    const markers = [];
    busItems.forEach(li => {
      const lat = parseFloat(li.dataset.lat);
      const lng = parseFloat(li.dataset.lng);
      const txt = li.textContent;
      const marker = L.marker([lat, lng]).addTo(map).bindPopup(txt);
      markers.push(marker);
      li.addEventListener('click', () => {
        map.setView([lat, lng], 15, {animate:true});
        marker.openPopup();
      });
    });

    // simple animation loop to simulate movement
    setInterval(() => {
      markers.forEach(m => {
        const pos = m.getLatLng();
        const newLat = pos.lat + (Math.random()-0.5) * 0.0015;
        const newLng = pos.lng + (Math.random()-0.5) * 0.0015;
        m.setLatLng([newLat, newLng]);
      });
    }, 3000);
  }
});
