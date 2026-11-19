(() => {
  const bounds = JSON.parse(document.getElementById('time-bounds').textContent);
  if (!bounds) return;

  const control = document.getElementById('charts-time-range');
  const menu = document.getElementById('range-menu');
  const trigger = document.getElementById('range-trigger');
  const label = document.getElementById('range-label');
  const form = document.getElementById('range-form');
  const startInput = document.getElementById('range-start');
  const endInput = document.getElementById('range-end');
  const error = document.getElementById('range-error');
  const summary = document.getElementById('range-summary');
  const presets = Array.from(control.querySelectorAll('[data-range]'));
  const durations = {
    '5m': 300000, '15m': 900000, '30m': 1800000,
    '1h': 3600000, '2h': 7200000, '3h': 10800000, '6h': 21600000,
    '12h': 43200000, '24h': 86400000,
  };
  const formatter = new Intl.DateTimeFormat(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: 'numeric', minute: '2-digit', second: '2-digit',
  });
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  document.getElementById('range-timezone').textContent = `Browser time · ${timezone}`;

  function localInputValue(timestamp) {
    const date = new Date(timestamp);
    const local = new Date(timestamp - date.getTimezoneOffset() * 60000);
    return local.toISOString().slice(0, 19);
  }

  const params = new URL(window.location.href).searchParams;
  let start = Date.parse(params.get('start'));
  let end = Date.parse(params.get('end'));
  let selected = params.get('range');
  let boundsRequest;
  if (selected === 'all') {
    start = bounds.start;
    end = bounds.end;
  } else if (Object.hasOwn(durations, selected)) {
    end = Date.now();
    start = end - durations[selected];
  } else if (selected !== null || !Number.isFinite(start) || !Number.isFinite(end) || start > end) {
    selected = '3h';
    end = Date.now();
    start = end - durations[selected];
  } else {
    selected = null;
  }

  function applyRange(saveUrl, updateInputs = true) {
    if (updateInputs) {
      startInput.value = localInputValue(start);
      endInput.value = localInputValue(end);
      error.textContent = '';
    }
    const activePreset = presets.find(button => button.dataset.range === selected);
    const exactRange = `${formatter.format(start)} – ${formatter.format(end)}`;
    label.textContent = activePreset ? activePreset.textContent : exactRange;
    trigger.title = `${exactRange} (${timezone})`;
    for (const button of presets) {
      button.setAttribute('aria-pressed', String(button.dataset.range === selected));
    }
    const range = { start: new Date(start).toISOString(), end: new Date(end).toISOString() };
    control.dataset.start = range.start;
    control.dataset.end = range.end;
    summary.textContent = exactRange;
    if (saveUrl) {
      const url = new URL(window.location.href);
      url.searchParams.set('start', range.start);
      url.searchParams.set('end', range.end);
      if (selected) url.searchParams.set('range', selected);
      else url.searchParams.delete('range');
      window.history.replaceState(null, '', url);
    }
    control.dispatchEvent(new CustomEvent('charts:range-change', { bubbles: true, detail: range }));
  }

  function closeMenu() {
    menu.open = false;
    trigger.focus();
  }

  for (const button of presets) {
    button.addEventListener('click', () => {
      boundsRequest?.abort();
      boundsRequest = null;
      selected = button.dataset.range;
      end = selected === 'all' ? bounds.end : Date.now();
      start = selected === 'all' ? bounds.start : end - durations[selected];
      applyRange(true);
      closeMenu();
    });
  }
  form.addEventListener('submit', event => {
    event.preventDefault();
    const from = new Date(startInput.value).getTime();
    const to = new Date(endInput.value).getTime();
    if (!Number.isFinite(from) || !Number.isFinite(to) || from > to) {
      error.textContent = 'Choose a valid From date that is before the To date.';
      return;
    }
    start = from;
    end = to;
    selected = null;
    boundsRequest?.abort();
    boundsRequest = null;
    applyRange(true);
    closeMenu();
  });
  document.addEventListener('click', event => {
    if (!control.contains(event.target)) menu.open = false;
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && menu.open) closeMenu();
  });
  menu.addEventListener('toggle', () => {
    if (menu.open) {
      startInput.value = localInputValue(start);
      endInput.value = localInputValue(end);
      error.textContent = '';
    }
  });
  document.addEventListener('charts:refresh-request', async () => {
    boundsRequest?.abort();
    const request = new AbortController();
    boundsRequest = request;
    const timeout = setTimeout(() => request.abort(), 45000);
    try {
      if (selected === 'all') {
        const url = JSON.parse(document.getElementById('time-bounds-url').textContent);
        const response = await fetch(url, { signal: request.signal, cache: 'no-store' });
        const updated = await response.json();
        if (request.signal.aborted) return;
        if (!response.ok || !updated) throw new Error('Unable to refresh time bounds');
        bounds.start = updated.start;
        bounds.end = updated.end;
        start = bounds.start;
        end = bounds.end;
      } else if (selected) {
        end = Date.now();
        start = end - durations[selected];
      }
      if (!request.signal.aborted) applyRange(true, !menu.open);
    } catch {
      if (boundsRequest === request) {
        document.dispatchEvent(new CustomEvent('charts:refreshed', { detail: { success: false } }));
      }
    } finally {
      clearTimeout(timeout);
    }
  });
  applyRange(false);
})();
