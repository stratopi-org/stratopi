const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { runInNewContext } = require('node:vm');

function collection(ids = ['one', 'two']) {
  return { type: 'FeatureCollection', features: ids.map((id, index) => ({
    type: 'Feature', id, geometry: { type: 'Point', coordinates: [-87.6 + index * .01, 41.8] },
    properties: { added: '2026-11-19T12:00:00Z', altitude_m: 140, vertical_speed_mpm: null,
      speed_kn: 0, course_d: 0, direction: 'N' },
  })) };
}

function setup(fetcher = async () => ({ ok: true, json: async () => collection() }), key = 'test-browser-key', loadMode = 'existing') {
  const calls = [];
  const handlers = {};
  const elements = {};
  for (const id of ['location-map-panel', 'location-map', 'location-map-status', 'location-map-fit', 'google-maps-config']) {
    elements[id] = { hidden: true, disabled: true, textContent: '', dataset: { mapUrl: '/api/charts/location/map' },
      setAttribute() {}, addEventListener: (name, callback) => { handlers[id] = callback; } };
  }
  elements['google-maps-config'].textContent = JSON.stringify({ apiKey: key });
  class Bounds {
    constructor() { this.points = []; }
    extend(point) { this.points.push(point); }
    isEmpty() { return this.points.length === 0; }
    getNorthEast() { return { equals: () => this.points.every(point =>
      point.lat === this.points[0].lat && point.lng === this.points[0].lng) }; }
    getSouthWest() { return this.points[0]; }
  }
  const features = new Map();
  const dataLayer = {
    setStyle() {}, addListener: (name, callback) => { handlers.mapClick = callback; },
    remove(feature) { features.delete(feature.getId()); calls.push(['remove', feature.getId()]); },
    addGeoJson(value) {
      calls.push(['add', value.features.length]);
      return value.features.map(item => {
        const feature = { getId: () => item.id, getProperty: name => item.properties[name] };
        features.set(item.id, feature);
        return feature;
      });
    },
  };
  const maps = {
    Map: class {
      constructor() { this.data = dataLayer; calls.push(['createMap']); }
      fitBounds() { calls.push(['fit']); }
      setCenter() { calls.push(['center']); }
      setZoom(zoom) { calls.push(['zoom', zoom]); }
    },
    InfoWindow: class { close() {} setContent(content) { calls.push(['popup', content]); }
      setPosition() {} open() {} },
    LatLngBounds: Bounds, SymbolPath: { CIRCLE: 'circle' },
  };
  const window = { location: { origin: 'http://localhost:5500' } };
  if (loadMode === 'existing') window.google = { maps };
  runInNewContext(readFileSync(join(__dirname, '../static/location-map.js'), 'utf8'), {
    document: {
      getElementById: id => elements[id],
      createElement: () => ({ children: [], appendChild(child) { this.children.push(child); }, remove() {} }),
      head: { appendChild(script) {
        calls.push(['script', script.src]);
        setImmediate(() => {
          if (loadMode === 'error') script.onerror();
          else {
            window.google = { maps };
            window.dashboardMapsReady();
          }
        });
      } },
    }, window, URL, AbortController, setTimeout, clearTimeout,
    fetch: (...args) => { calls.push(['fetch', ...args]); return fetcher(...args); },
  });
  return { window, elements, calls, features, handlers,
    update: (viewKey = '3h', controller = new AbortController()) => window.DashboardLocationMap.update({
      start: '2026-11-19T12:00:00Z', end: '2026-11-19T15:00:00Z', viewKey,
    }, controller.signal),
  };
}

test('requests shared dates and renders each location while reusing the map and unchanged points', async () => {
  const state = setup();
  assert.equal(await state.update(), true);
  assert.deepEqual([...state.features.keys()], ['one', 'two']);
  const request = state.calls.find(call => call[0] === 'fetch');
  assert.equal(request[1].searchParams.get('start'), '2026-11-19T12:00:00Z');
  assert.equal(request[1].searchParams.get('end'), '2026-11-19T15:00:00Z');
  await state.update();
  assert.equal(state.calls.filter(call => call[0] === 'createMap').length, 1);
  assert.equal(state.calls.filter(call => call[0] === 'add').length, 1);
  assert.equal(state.calls.filter(call => call[0] === 'fit').length, 1);
  await state.update('6h');
  assert.equal(state.calls.filter(call => call[0] === 'fit').length, 2);
});

test('a new range removes old points and empty ranges clear every point', async () => {
  let ids = ['one', 'two'];
  const state = setup(async () => ({ ok: true, json: async () => collection(ids) }));
  await state.update();
  ids = ['two'];
  await state.update('6h');
  assert.deepEqual([...state.features.keys()], ['two']);
  ids = [];
  await state.update('24h');
  assert.equal(state.features.size, 0);
  assert.equal(state.elements['location-map-fit'].disabled, true);
  assert.match(state.elements['location-map-status'].textContent, /No valid locations/);
});

test('stale responses cannot replace the latest filtered points', async () => {
  let complete;
  let count = 0;
  const state = setup(async () => {
    if (++count === 1) return new Promise(resolve => { complete = resolve; });
    return { ok: true, json: async () => collection(['latest']) };
  });
  const controller = new AbortController();
  const first = state.update('3h', controller);
  controller.abort();
  await state.update('6h');
  complete({ ok: true, json: async () => collection(['stale']) });
  await first;
  assert.deepEqual([...state.features.keys()], ['latest']);
});

test('point popups use safe text and retain zero and NULL values', async () => {
  const state = setup();
  await state.update();
  state.handlers.mapClick({ feature: state.features.get('one'), latLng: {} });
  const popup = state.calls.find(call => call[0] === 'popup')[1];
  const lines = popup.children.map(child => child.textContent);
  assert.ok(lines.includes('vertical_speed_mpm: NULL'));
  assert.ok(lines.includes('speed_kn: 0'));
});

test('missing configuration and backend failures have safe states', async () => {
  const missing = setup(undefined, '');
  assert.equal(missing.window.DashboardLocationMap, undefined);
  assert.equal(missing.calls.length, 0);
  const failed = setup(async () => ({ ok: false, json: async () => ({ error: 'Unable to load locations.' }) }));
  assert.equal(await failed.update(), false);
  assert.equal(failed.elements['location-map'].hidden, true);
  assert.equal(failed.elements['location-map-status'].textContent, 'Unable to load locations.');
});

test('loads the Google API once using its callback and reports script failures', async () => {
  const state = setup(undefined, 'test-browser-key', 'ready');
  assert.equal(await state.update(), true);
  await state.update();
  assert.equal(state.calls.filter(call => call[0] === 'script').length, 1);
  const url = new URL(state.calls.find(call => call[0] === 'script')[1]);
  assert.equal(url.origin, 'https://maps.googleapis.com');
  assert.equal(url.searchParams.get('callback'), 'dashboardMapsReady');
  const failed = setup(undefined, 'test-browser-key', 'error');
  assert.equal(await failed.update(), false);
  assert.match(failed.elements['location-map-status'].textContent, /Unable to load Google Maps/);
});
