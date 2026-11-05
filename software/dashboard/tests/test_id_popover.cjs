const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { runInNewContext } = require('node:vm');

function setup(writeText) {
  const events = {};
  const timers = new Map();
  const tooltip = {
    style: {}, hidden: true, textContent: '',
    contains: () => false,
    getBoundingClientRect: () => ({ width: 320, height: 40 }),
  };
  const notification = { textContent: '' };
  const document = {
    getElementById: id => id === 'id-popover' ? tooltip : notification,
    addEventListener: (name, callback) => { events[name] = callback; },
  };
  let timerId = 0;
  runInNewContext(readFileSync(join(__dirname, '../static/id-popover.js'), 'utf8'), {
    document, navigator: { clipboard: { writeText } },
    window: { innerWidth: 1000, innerHeight: 800, addEventListener() {} },
    setTimeout: callback => { timers.set(++timerId, callback); return timerId; },
    clearTimeout: id => timers.delete(id),
  });
  const trigger = {
    dataset: { id: '12345678-1234-1234-1234-123456789abc' },
    getBoundingClientRect: () => ({ left: 50, top: 50, bottom: 82 }),
  };
  return { events, trigger, tooltip, notification, timers };
}

test('click copies full ID, announces success, then clears the notification', async () => {
  const copied = [];
  const state = setup(async value => { copied.push(value); });
  state.events.click({ target: { closest: () => state.trigger } });
  await new Promise(setImmediate);
  assert.deepEqual(copied, [state.trigger.dataset.id]);
  assert.equal(state.tooltip.textContent, state.trigger.dataset.id);
  assert.equal(state.notification.textContent, 'id copied to clipboard.');
  for (const callback of state.timers.values()) callback();
  assert.equal(state.notification.textContent, '');
});

test('clipboard failure reports an error instead of success', async () => {
  const state = setup(async () => { throw new Error('denied'); });
  state.events.click({ target: { closest: () => state.trigger } });
  await new Promise(setImmediate);
  assert.match(state.notification.textContent, /Unable to copy/);
  assert.equal(state.tooltip.hidden, false);
});

test('hover reveals the ID without copying it', () => {
  const state = setup(() => { assert.fail('hover must not copy'); });
  state.events.pointerover({ target: { closest: () => state.trigger } });
  assert.equal(state.tooltip.textContent, state.trigger.dataset.id);
  assert.equal(state.notification.textContent, '');
});
