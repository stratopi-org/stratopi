const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { runInNewContext } = require('node:vm');

function setup(saved = null, fetcher = async () => ({ ok: true, text: async () => '<html>' })) {
  const timers = new Map();
  const calls = [];
  const listeners = {};
  const select = { value: '0', addEventListener: (_, fn) => { listeners.change = fn; } };
  const status = { textContent: '' };
  const content = {
    contains: () => false, querySelectorAll: () => [],
    replaceChildren: (...nodes) => { calls.push(['replace', nodes]); },
  };
  const elements = { 'auto-refresh': select,
    'refresh-status': status, 'table-data': content };
  const storage = { value: saved, getItem() { return this.value; }, setItem(_, value) { this.value = value; } };
  let timerId = 0;
  let now = 0;
  const url = 'http://localhost:5000/?page%3A%5B%22public%22%2C%22sensors%22%5D=2#table-1';
  runInNewContext(readFileSync(join(__dirname, '../static/auto-refresh.js'), 'utf8'), {
    document: {
      getElementById: id => elements[id], importNode: node => node,
      dispatchEvent: event => calls.push(['event', event.type]),
    },
    window: { location: { href: url }, scrollX: 0, scrollY: 500,
      scrollTo: position => calls.push(['scroll', position.top]) },
    DOMParser: class { parseFromString() { return { getElementById: () => ({ childNodes: ['fresh tables'] }) }; } },
    fetch: (...args) => { calls.push(['fetch', ...args]); return fetcher(...args); },
    localStorage: storage, AbortController, Event,
    Date: { now: () => now },
    setTimeout: (fn, delay) => { timers.set(++timerId, { fn, delay }); return timerId; },
    clearTimeout: id => timers.delete(id),
  });
  return { timers, calls, listeners, select, status, storage, url,
    choose(value) { select.value = value; listeners.change(); },
    async tick(delay) {
      const [id, timer] = [...timers].find(([, timer]) => timer.delay === delay);
      timers.delete(id);
      now += delay;
      timer.fn();
      await new Promise(setImmediate);
    },
  };
}

test('defaults to Never and supports all intervals with persisted selection', async () => {
  const state = setup();
  assert.equal(state.timers.size, 0);
  for (const seconds of ['5', '15', '30', '60']) {
    state.choose(seconds);
    await new Promise(setImmediate);
    assert.ok([...state.timers.values()].some(timer => timer.delay === Number(seconds) * 1000));
    assert.equal(state.storage.value, seconds);
  }
  state.choose('0');
  assert.equal(state.timers.size, 0);
});

test('Never to enabled refreshes immediately and resets the elapsed-time clock each time', async () => {
  const state = setup();
  state.choose('15');
  assert.equal(state.calls.filter(call => call[0] === 'fetch').length, 1);
  await new Promise(setImmediate);
  assert.equal(state.status.textContent, 'Data refreshed 0 seconds ago');
  await state.tick(1000);
  assert.equal(state.status.textContent, 'Data refreshed 1 second ago');
  state.choose('0');
  assert.equal(state.status.textContent, '');
  assert.equal(state.timers.size, 0);
  state.choose('15');
  assert.equal(state.calls.filter(call => call[0] === 'fetch').length, 2);
  await new Promise(setImmediate);
  assert.equal(state.status.textContent, 'Data refreshed 0 seconds ago');
  await state.tick(15000);
  assert.equal(state.calls.filter(call => call[0] === 'fetch').length, 3);
  assert.equal(state.status.textContent, 'Data refreshed 0 seconds ago');
});

test('poll replaces data in place using the current pagination URL and restores scroll', async () => {
  const state = setup('15');
  await state.tick(15000);
  assert.equal(state.calls.find(call => call[0] === 'fetch')[1], state.url);
  assert.equal(state.calls.find(call => call[0] === 'replace')[1][0], 'fresh tables');
  assert.equal(state.calls.find(call => call[0] === 'scroll')[1], 500);
  assert.equal(state.status.textContent, 'Data refreshed 0 seconds ago');
  assert.ok([...state.timers.values()].some(timer => timer.delay === 15000));
  await state.tick(1000);
  assert.equal(state.status.textContent, 'Data refreshed 1 second ago');
  await state.tick(1000);
  assert.equal(state.status.textContent, 'Data refreshed 2 seconds ago');
  await state.tick(15000);
  assert.equal(state.status.textContent, 'Data refreshed 0 seconds ago');
});

test('failed refresh retains data and schedules a retry', async () => {
  const state = setup('30', async () => ({ ok: false }));
  await state.tick(30000);
  assert.equal(state.calls.some(call => call[0] === 'replace'), false);
  assert.match(state.status.textContent, /Existing data is unchanged/);
  assert.equal([...state.timers.values()][0].delay, 30000);
});

test('selecting Never clears the elapsed-time message and stops all timers', async () => {
  const state = setup('15');
  await state.tick(15000);
  await state.tick(1000);
  assert.equal(state.status.textContent, 'Data refreshed 1 second ago');
  state.choose('0');
  assert.equal(state.status.textContent, '');
  assert.equal(state.timers.size, 0);
});

test('selecting Never aborts an in-flight request without applying stale data', async () => {
  let complete;
  const state = setup('15', () => new Promise(resolve => { complete = resolve; }));
  await state.tick(15000);
  const request = state.calls.find(call => call[0] === 'fetch')[2];
  state.choose('0');
  assert.equal(request.signal.aborted, true);
  complete({ ok: true, text: async () => '<html>' });
  await new Promise(setImmediate);
  assert.equal(state.calls.some(call => call[0] === 'replace'), false);
  assert.equal(state.timers.size, 0);
});
