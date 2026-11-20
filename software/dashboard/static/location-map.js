(() => {
  const panel = document.getElementById('location-map-panel');
  const config = JSON.parse(document.getElementById('google-maps-config').textContent);
  if (!panel || !config.apiKey) return;

  const canvas = document.getElementById('location-map');
  const status = document.getElementById('location-map-status');
  const fitButton = document.getElementById('location-map-fit');
  let apiPromise;
  let map;
  let infoWindow;
  let currentBounds;
  let lastViewKey;
  let authError;
  let activeSignal;
  const rendered = new Map();

  function loadApi() {
    if (authError) return Promise.reject(authError);
    if (window.google?.maps?.Map) return Promise.resolve(window.google.maps);
    if (apiPromise) return apiPromise;
    apiPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      const timeout = setTimeout(() => fail('Google Maps timed out. Check your connection and API key.'), 30000);
      function fail(message) {
        clearTimeout(timeout);
        script.remove();
        reject(new Error(message));
      }
      window.dashboardMapsReady = () => {
        clearTimeout(timeout);
        resolve(window.google.maps);
      };
      window.gm_authFailure = () => {
        authError = new Error('Google Maps authorization failed. Check the API key, billing, and website restrictions.');
        status.textContent = authError.message;
        canvas.hidden = true;
        fail(authError.message);
      };
      const url = new URL('https://maps.googleapis.com/maps/api/js');
      url.searchParams.set('key', config.apiKey);
      url.searchParams.set('v', 'quarterly');
      url.searchParams.set('loading', 'async');
      url.searchParams.set('callback', 'dashboardMapsReady');
      script.src = url.href;
      script.async = true;
      script.onerror = () => fail('Unable to load Google Maps. Check your network connection.');
      document.head.appendChild(script);
    }).catch(error => {
      apiPromise = null;
      throw error;
    });
    return apiPromise;
  }

  function showReading(event) {
    const content = document.createElement('div');
    content.className = 'location-map-info';
    const fields = [
      ['added', new Date(event.feature.getProperty('added')).toLocaleString()],
      ['altitude_m', event.feature.getProperty('altitude_m')],
      ['vertical_speed_mpm', event.feature.getProperty('vertical_speed_mpm')],
      ['speed_kn', event.feature.getProperty('speed_kn')],
      ['course_d', event.feature.getProperty('course_d')],
      ['direction', event.feature.getProperty('direction')],
    ];
    for (const [name, value] of fields) {
      const line = document.createElement('p');
      line.textContent = `${name}: ${value ?? 'NULL'}`;
      content.appendChild(line);
    }
    infoWindow.setContent(content);
    infoWindow.setPosition(event.latLng);
    infoWindow.open({ map, shouldFocus: false });
  }

  function fitLocations() {
    if (!currentBounds || currentBounds.isEmpty()) return;
    const northeast = currentBounds.getNorthEast();
    const southwest = currentBounds.getSouthWest();
    if (northeast.equals(southwest)) {
      map.setCenter(northeast);
      map.setZoom(16);
    } else {
      map.fitBounds(currentBounds, 40);
    }
  }
  fitButton.addEventListener('click', fitLocations);

  function initializeMap(maps) {
    if (map) return;
    map = new maps.Map(canvas, {
      center: { lat: 0, lng: 0 }, zoom: 2, gestureHandling: 'cooperative',
      styles: [
        { elementType: 'geometry', stylers: [{ color: '#202c3b' }] },
        { elementType: 'labels.text.stroke', stylers: [{ color: '#161e29' }] },
        { elementType: 'labels.text.fill', stylers: [{ color: '#a3b1c2' }] },
        { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#354357' }] },
        { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#10263d' }] },
      ],
    });
    map.data.setStyle({
      icon: { path: maps.SymbolPath.CIRCLE, scale: 5, fillColor: '#88c7ff',
        fillOpacity: 0.9, strokeColor: '#161e29', strokeWeight: 1 },
    });
    map.data.addListener('click', showReading);
    infoWindow = new maps.InfoWindow();
  }

  function updateFeatures(collection, maps) {
    infoWindow.close();
    const ids = new Set(collection.features.map(feature => String(feature.id)));
    for (const [id, entry] of rendered) {
      if (!ids.has(id)) {
        map.data.remove(entry.feature);
        rendered.delete(id);
      }
    }
    const additions = [];
    currentBounds = new maps.LatLngBounds();
    for (const feature of collection.features) {
      const id = String(feature.id);
      const signature = JSON.stringify(feature);
      const existing = rendered.get(id);
      const [lng, lat] = feature.geometry.coordinates;
      currentBounds.extend({ lat, lng });
      if (existing?.signature === signature) continue;
      if (existing) map.data.remove(existing.feature);
      rendered.set(id, { signature });
      additions.push(feature);
    }
    if (additions.length) {
      for (const feature of map.data.addGeoJson({ type: 'FeatureCollection', features: additions })) {
        rendered.get(String(feature.getId())).feature = feature;
      }
    }
  }

  window.DashboardLocationMap = {
    async update(range, signal) {
      const fetchController = new AbortController();
      const abortFetch = () => fetchController.abort();
      signal.addEventListener('abort', abortFetch, { once: true });
      if (signal.aborted) abortFetch();
      activeSignal = signal;
      panel.setAttribute('aria-busy', 'true');
      status.textContent = 'Loading locations…';
      try {
        const url = new URL(panel.dataset.mapUrl, window.location.origin);
        url.searchParams.set('start', range.start);
        url.searchParams.set('end', range.end);
        const [maps, response] = await Promise.all([
          loadApi(), fetch(url, { signal: fetchController.signal, cache: 'no-store' }),
        ]);
        const collection = await response.json();
        if (signal.aborted) return false;
        if (!response.ok) throw new Error(collection.error || 'Unable to load locations.');
        if (authError) throw authError;
        canvas.hidden = false;
        initializeMap(maps);
        updateFeatures(collection, maps);
        fitButton.disabled = collection.features.length === 0;
        const viewKey = range.viewKey || `${range.start}/${range.end}`;
        if (collection.features.length && lastViewKey !== viewKey) {
          fitLocations();
          lastViewKey = viewKey;
        }
        status.textContent = collection.features.length
          ? `${collection.features.length} location${collection.features.length === 1 ? '' : 's'}. Select a point for reading details.`
          : 'No valid locations in this time range.';
        return true;
      } catch (error) {
        if (activeSignal !== signal) return false;
        canvas.hidden = true;
        fitButton.disabled = true;
        status.textContent = signal.aborted ? 'Location request timed out.' : error.message;
        return false;
      } finally {
        fetchController.abort();
        signal.removeEventListener('abort', abortFetch);
        if (activeSignal === signal) panel.setAttribute('aria-busy', 'false');
      }
    },
  };
})();
