const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { runInNewContext } = require('node:vm');

function setup(query = '', bounds = { start: 1700000000000, end: 1700086400000 }, fetcher = async () => ({
  ok: true, json: async () => ({ start: 1600000000000, end: 1800000000000 }),
})) {
  const events = [];
  const elements = {};
  function element(dataset = {}) {
    return {
      dataset, value: '', textContent: '', open: false, handlers: {}, attributes: {},
      setAttribute(name, value) { this.attributes[name] = value; },
      addEventListener(name, callback) { this.handlers[name] = callback; },
      dispatchEvent(event) { events.push(event); },
      contains() { return false; }, focus() {},
    };
  }
  for (const id of ['time-bounds', 'charts-time-range', 'range-menu', 'range-trigger',
    'range-label', 'range-form', 'range-start', 'range-end', 'range-error',
    'range-summary', 'range-timezone', 'time-bounds-url']) elements[id] = element();
  const presets = ['5m', '15m', '30m', '1h', '2h', '3h', '6h', '12h', '24h', 'all'].map(key => {
    const button = element({ range: key });
    button.textContent = key === '3h' ? 'Last 3 hours' : `Last ${key}`;
    return button;
  });
  elements['charts-time-range'].querySelectorAll = () => presets;
  elements['time-bounds'].textContent = JSON.stringify(bounds);
  elements['time-bounds-url'].textContent = JSON.stringify('/api/charts/time-bounds');
  const location = { href: 'http://localhost:5500/' + query };
  const documentEvents = {};
  let now = Date.now();
  class ClockDate extends Date { static now() { return now; } }
  runInNewContext(readFileSync(join(__dirname, '../static/charts-time-range.js'), 'utf8'), {
    document: { getElementById: id => elements[id],
      dispatchEvent: event => events.push(event),
      addEventListener(name, callback) { documentEvents[name] = callback; } },
    window: { location, history: { replaceState(_, __, url) { location.href = url.href; } } },
    URL, Intl, Date: ClockDate, AbortController, setTimeout, clearTimeout, fetch: fetcher,
    CustomEvent: class { constructor(name, options) { this.type = name; Object.assign(this, options); } },
  });
  return { elements, events, location, bounds, documentEvents,
    advance(milliseconds) { now += milliseconds; },
    refresh() { return documentEvents['charts:refresh-request'](); },
    preset(key) { presets.find(button => button.dataset.range === key).handlers.click(); },
    apply(start, end) {
      elements['range-start'].value = start;
      elements['range-end'].value = end;
      elements['range-form'].handlers.submit({ preventDefault() {} });
    },
  };
}

test('defaults to the last 3 hours and prefills the absolute range', () => {
  const state = setup();
  assert.equal(state.elements['range-label'].textContent, 'Last 3 hours');
  assert.equal(state.events[0].type, 'charts:range-change');
  const range = state.events[0].detail;
  assert.equal(Date.parse(range.end) - Date.parse(range.start), 10800000);
  assert.ok(Math.abs(Date.now() - Date.parse(range.end)) < 1000);
  assert.equal(new Date(state.elements['range-end'].value) - new Date(state.elements['range-start'].value), 10800000);
});

test('an explicit URL range restores 2 hours independently of browser storage', () => {
  const state = setup('?range=2h');
  const range = state.events[0].detail;
  assert.equal(Date.parse(range.end) - Date.parse(range.start), 7200000);
  const clean = setup();
  assert.equal(clean.elements['range-label'].textContent, 'Last 3 hours');
  assert.equal(Date.parse(clean.events[0].detail.end) - Date.parse(clean.events[0].detail.start), 10800000);
});

test('auto refresh advances relative ranges and keeps custom dates fixed', async () => {
  const state = setup();
  const first = state.events.at(-1).detail;
  state.advance(15000);
  await state.refresh();
  assert.equal(Date.parse(state.events.at(-1).detail.end) - Date.parse(first.end), 15000);
  state.apply('2026-11-19T12:00', '2026-11-19T15:00');
  const custom = JSON.stringify(state.events.at(-1).detail);
  state.advance(15000);
  await state.refresh();
  assert.equal(JSON.stringify(state.events.at(-1).detail), custom);
});

test('auto refresh of all data reloads the available database bounds', async () => {
  const state = setup('?range=all');
  await state.refresh();
  assert.equal(Date.parse(state.events.at(-1).detail.start), 1600000000000);
  assert.equal(Date.parse(state.events.at(-1).detail.end), 1800000000000);
});

test('background refresh leaves draft custom dates alone while picker is open', async () => {
  const state = setup();
  state.elements['range-menu'].open = true;
  state.elements['range-start'].value = '2026-11-01T12:00';
  state.advance(5000);
  await state.refresh();
  assert.equal(state.elements['range-start'].value, '2026-11-01T12:00');
});

test('failed bounds refresh signals failure so polling can retry', async () => {
  const state = setup('?range=all', undefined, async () => ({ ok: false, json: async () => ({ error: 'unavailable' }) }));
  await state.refresh();
  assert.equal(state.events.at(-1).type, 'charts:refreshed');
  assert.equal(state.events.at(-1).detail.success, false);
});

test('quick ranges end at now and persist their relative selection', () => {
  const state = setup();
  state.elements['range-menu'].open = true;
  state.preset('6h');
  const range = state.events.at(-1).detail;
  assert.equal(Date.parse(range.end) - Date.parse(range.start), 21600000);
  assert.ok(Math.abs(Date.now() - Date.parse(range.end)) < 1000);
  assert.equal(new URL(state.location.href).searchParams.get('range'), '6h');
  assert.equal(state.elements['range-menu'].open, false);
  state.preset('5m');
  const minuteRange = state.events.at(-1).detail;
  assert.equal(Date.parse(minuteRange.end) - Date.parse(minuteRange.start), 300000);
});

test('custom dates apply only on submission and reversed dates are rejected', () => {
  const state = setup('?range=6h');
  const before = state.events.length;
  state.apply('2026-11-20T12:00', '2026-11-19T12:00');
  assert.equal(state.events.length, before);
  assert.match(state.elements['range-error'].textContent, /before/);
  state.apply('2026-11-19T12:00', '2026-11-20T12:00');
  assert.equal(state.events.length, before + 1);
  const params = new URL(state.location.href).searchParams;
  assert.equal(params.has('range'), false);
  assert.equal(params.get('start'), new Date('2026-11-19T12:00').toISOString());
  assert.equal(state.elements['range-error'].textContent, '');
});

test('restores custom URL dates and resolves relative dates on reload', () => {
  const state = setup('?start=2026-11-01T00:00:00Z&end=2026-11-02T00:00:00Z');
  assert.equal(state.events[0].detail.start, '2026-11-01T00:00:00.000Z');
  const relative = setup('?range=6h&start=2000-01-01&end=2000-01-02');
  assert.ok(Math.abs(Date.now() - Date.parse(relative.events[0].detail.end)) < 1000);
  assert.equal(setup('?start=invalid&end=invalid').elements['range-label'].textContent, 'Last 3 hours');
});

test('retired presets in old URLs fall back to the 3-hour default', () => {
  for (const range of ['1m', '7d', '30d']) {
    const state = setup(`?range=${range}&start=2000-01-01&end=2000-02-01`);
    assert.equal(state.elements['range-label'].textContent, 'Last 3 hours');
    const selection = state.events[0].detail;
    assert.equal(Date.parse(selection.end) - Date.parse(selection.start), 10800000);
  }
});

test('all data uses the database time bounds on selection and reload', () => {
  const state = setup();
  state.preset('all');
  const range = state.events.at(-1).detail;
  assert.equal(Date.parse(range.start), state.bounds.start);
  assert.equal(Date.parse(range.end), state.bounds.end);
  assert.equal(new URL(state.location.href).searchParams.get('range'), 'all');
  const restored = setup('?range=all&start=2000-01-01&end=2000-01-02');
  assert.equal(Date.parse(restored.events[0].detail.start), restored.bounds.start);
  assert.equal(Date.parse(restored.events[0].detail.end), restored.bounds.end);
});

test('Escape and outside clicks dismiss the picker and empty data initializes safely', () => {
  assert.equal(setup('', null).events.length, 0);
  const state = setup();
  const menu = state.elements['range-menu'];
  menu.open = true;
  state.documentEvents.keydown({ key: 'Escape' });
  assert.equal(menu.open, false);
  menu.open = true;
  state.documentEvents.click({ target: {} });
  assert.equal(menu.open, false);
});
