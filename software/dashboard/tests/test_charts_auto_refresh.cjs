const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { runInNewContext } = require('node:vm');

function setup(saved = null) {
  const timers = new Map();
  const events = [];
  const listeners = {};
  const select = { value: '0', addEventListener: (_, callback) => { listeners.change = callback; } };
  const status = { textContent: '' };
  const storage = { value: saved, getItem() { return this.value; }, setItem(_, value) { this.value = value; } };
  let now = 0;
  let timerId = 0;
  runInNewContext(readFileSync(join(__dirname, '../static/charts-auto-refresh.js'), 'utf8'), {
    document: {
      getElementById: id => id === 'charts-auto-refresh' ? select : status,
      addEventListener: (name, callback) => { listeners[name] = callback; },
      dispatchEvent: event => events.push(event),
    },
    localStorage: storage, Date: { now: () => now },
    CustomEvent: class { constructor(type) { this.type = type; } },
    setTimeout: (callback, delay) => { timers.set(++timerId, { callback, delay }); return timerId; },
    clearTimeout: id => timers.delete(id),
  });
  return { timers, events, select, status, storage,
    choose(value) { select.value = value; listeners.change(); },
    loading() { listeners['charts:loading'](); },
    finish(success = true) { listeners['charts:refreshed']({ detail: { success } }); },
    tick(delay) {
      const [id, timer] = [...timers].find(([, timer]) => timer.delay === delay);
      timers.delete(id);
      now += delay;
      timer.callback();
    },
  };
}

test('missing or invalid saved preferences default to Never without scheduling refresh', () => {
  for (const saved of [null, '', 'invalid', '5']) {
    const state = setup(saved);
    assert.equal(state.select.value, '0');
    assert.equal(state.events.length, 0);
    assert.equal(state.timers.size, 0);
  }
});

test('all refresh options request an immediate update and wait for completion before scheduling', () => {
  for (const seconds of ['15', '30', '60', '120']) {
    const state = setup();
    state.choose(seconds);
    assert.equal(state.events.at(-1).type, 'charts:refresh-request');
    assert.equal(state.timers.size, 0);
    assert.equal(state.storage.value, seconds);
    state.finish();
    assert.ok([...state.timers.values()].some(timer => timer.delay === Number(seconds) * 1000));
    state.tick(Number(seconds) * 1000);
    assert.equal(state.events.length, 2);
    assert.equal(state.timers.size, 0);
  }
});

test('Never cancels timers and clears the seconds-ago status even if a batch completes later', () => {
  const state = setup();
  state.choose('15');
  state.finish();
  state.tick(1000);
  assert.equal(state.status.textContent, 'Data refreshed 1 second ago');
  state.choose('0');
  state.finish();
  assert.equal(state.status.textContent, '');
  assert.equal(state.timers.size, 0);
});

test('saved interval starts after initial charts finish and failures retry without a success timestamp', () => {
  const state = setup('15');
  assert.equal(state.select.value, '15');
  assert.equal(state.timers.size, 0);
  state.loading();
  state.finish(false);
  assert.match(state.status.textContent, /Unable to refresh/);
  state.tick(15000);
  assert.equal(state.events.at(-1).type, 'charts:refresh-request');
  state.finish();
  assert.equal(state.status.textContent, 'Data refreshed 0 seconds ago');
});

test('a manual time range change cancels the timer until the new chart batch finishes', () => {
  const state = setup('15');
  state.finish();
  state.loading();
  assert.equal(state.timers.size, 0);
  state.finish();
  assert.ok([...state.timers.values()].some(timer => timer.delay === 15000));
});
