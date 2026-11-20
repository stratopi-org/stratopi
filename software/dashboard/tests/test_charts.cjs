const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { runInNewContext } = require('node:vm');

function setup(fetcher, chartCount = 1, mapUpdater = null) {
  const calls = [];
  const listeners = {};
  const plot = { hidden: true };
  const status = { textContent: '' };
  const panel = {
    dataset: { chartUrl: '/api/charts/battery' },
    querySelector: selector => selector === '.chart-plot' ? plot : status,
    setAttribute: (key, value) => calls.push([key, value]),
  };
  const panels = [panel];
  for (let index = 1; index < chartCount; index++) {
    const extraPlot = { hidden: true };
    const extraStatus = { textContent: '' };
    panels.push({ ...panel, dataset: { chartUrl: `/api/charts/environmental/test-${index}` },
      querySelector: selector => selector === '.chart-plot' ? extraPlot : extraStatus });
  }
  runInNewContext(readFileSync(join(__dirname, '../static/charts.js'), 'utf8'), {
    document: { querySelectorAll: () => panels,
      dispatchEvent: event => calls.push(['event', event.type, event.detail]),
      addEventListener: (key, callback) => { (listeners[key] ||= []).push(callback); } },
    window: { location: { origin: 'http://localhost:5500' }, DashboardLocationMap: mapUpdater },
    fetch: (url, options) => { calls.push(['fetch', url, options]); return fetcher(url, options); },
    Plotly: { react: async (_, data, layout) => { calls.push(['render', data, layout]); } },
    URL, Date, Intl, AbortController, setTimeout, clearTimeout,
    CustomEvent: class { constructor(type, options) { this.type = type; this.detail = options?.detail; } },
  });
  return { calls, plot, status,
    change: (start, end) => Promise.all(listeners['charts:range-change'].map(callback => callback({ detail: { start, end } }))),
  };
}

function figure(count = 1) {
  return { data: [{ x: ['2026-11-19T12:00:00Z'], y: [80] }],
    layout: { xaxis: { range: ['2026-11-19T12:00:00Z', '2026-11-19T15:00:00Z'], title: {} },
      annotations: [{ xref: 'x', x: '2026-11-19T13:00:00Z', y: 80, text: '↑' }],
      meta: { row_count: count } } };
}

test('shared range events query the backend and render timestamps in browser time', async () => {
  const state = setup(async () => ({ ok: true, json: async () => figure() }));
  await state.change('2026-11-19T12:00:00Z', '2026-11-19T15:00:00Z');
  const url = state.calls.find(call => call[0] === 'fetch')[1];
  assert.equal(url.searchParams.get('start'), '2026-11-19T12:00:00Z');
  assert.equal(url.searchParams.get('end'), '2026-11-19T15:00:00Z');
  assert.equal(state.calls.filter(call => call[0] === 'render').length, 1);
  assert.ok(state.calls.find(call => call[0] === 'render')[1][0].x[0] instanceof Date);
  const arrowTime = state.calls.find(call => call[0] === 'render')[2].annotations[0].x;
  assert.ok(arrowTime instanceof Date);
  assert.equal(arrowTime.toISOString(), '2026-11-19T13:00:00.000Z');
  assert.equal(state.plot.hidden, false);
});

test('one shared range event reloads all six chart panels with the same dates', async () => {
  const state = setup(async () => ({ ok: true, json: async () => figure() }), 6);
  await state.change('2026-11-19T12:00:00Z', '2026-11-19T15:00:00Z');
  const requests = state.calls.filter(call => call[0] === 'fetch');
  assert.equal(requests.length, 6);
  assert.equal(new Set(requests.map(call => call[1].pathname)).size, 6);
  for (const request of requests) {
    assert.equal(request[1].searchParams.get('start'), '2026-11-19T12:00:00Z');
    assert.equal(request[1].searchParams.get('end'), '2026-11-19T15:00:00Z');
  }
  assert.equal(state.calls.filter(call => call[0] === 'render').length, 6);
});

test('a stale response cannot overwrite the newer time range', async () => {
  let completeFirst;
  let count = 0;
  const state = setup(async () => {
    if (++count === 1) return new Promise(resolve => { completeFirst = resolve; });
    return { ok: true, json: async () => figure() };
  });
  const first = state.change('2026-11-19T12:00:00Z', '2026-11-19T13:00:00Z');
  await state.change('2026-11-19T14:00:00Z', '2026-11-19T15:00:00Z');
  completeFirst({ ok: true, json: async () => figure() });
  await first;
  assert.equal(state.calls.filter(call => call[0] === 'render').length, 1);
  assert.equal(state.calls.find(call => call[0] === 'fetch')[2].signal.aborted, true);
});

test('the shared refresh batch waits for the map before reporting completion', async () => {
  let finishMap;
  const received = [];
  const mapUpdater = { update: (range, signal) => {
    received.push({ range, signal });
    return new Promise(resolve => { finishMap = resolve; });
  } };
  const state = setup(async () => ({ ok: true, json: async () => figure() }), 6, mapUpdater);
  const refresh = state.change('2026-11-19T12:00:00Z', '2026-11-19T15:00:00Z');
  await new Promise(setImmediate);
  assert.equal(received.length, 1);
  assert.equal(received[0].range.start, '2026-11-19T12:00:00Z');
  assert.equal(state.calls.some(call => call[0] === 'event' && call[1] === 'charts:refreshed'), false);
  finishMap(true);
  await refresh;
  assert.equal(state.calls.find(call => call[0] === 'event' && call[1] === 'charts:refreshed')[2].success, true);
});

test('empty ranges and backend errors display clear status messages', async () => {
  const empty = setup(async () => ({ ok: true, json: async () => figure(0) }));
  await empty.change('2026-11-19T12:00:00Z', '2026-11-19T15:00:00Z');
  assert.match(empty.status.textContent, /No data/);
  const error = setup(async () => ({ ok: false, json: async () => ({ error: 'Unable to load battery data.' }) }));
  await error.change('2026-11-19T12:00:00Z', '2026-11-19T15:00:00Z');
  assert.equal(error.plot.hidden, true);
  assert.equal(error.status.textContent, 'Unable to load battery data.');
});
