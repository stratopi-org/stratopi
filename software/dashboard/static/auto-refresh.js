(() => {
  const select = document.getElementById('auto-refresh');
  const status = document.getElementById('refresh-status');
  const content = document.getElementById('table-data');
  const storageKey = 'stratopi.autoRefreshSeconds';
  const allowed = ['0', '5', '15', '30', '60'];
  let timer;
  let controller;
  let ageTimer;
  let lastRefresh = null;

  function updateAge() {
    clearTimeout(ageTimer);
    if (select.value === '0' || lastRefresh === null) {
      status.textContent = '';
      return;
    }
    const seconds = Math.max(0, Math.floor((Date.now() - lastRefresh) / 1000));
    status.textContent = `Data refreshed ${seconds} ${seconds === 1 ? 'second' : 'seconds'} ago`;
    ageTimer = setTimeout(updateAge, 1000);
  }

  try {
    const saved = localStorage.getItem(storageKey);
    if (allowed.includes(saved)) select.value = saved;
  } catch { /* Refresh still works when browser storage is unavailable. */ }

  function schedule() {
    clearTimeout(timer);
    if (select.value !== '0') timer = setTimeout(refresh, Number(select.value) * 1000);
  }

  async function refresh() {
    if (controller) return;
    clearTimeout(timer);
    const request = new AbortController();
    controller = request;
    const timeout = setTimeout(() => request.abort(), 45000);
    clearTimeout(ageTimer);
    status.textContent = 'Refreshing...';
    try {
      const response = await fetch(window.location.href, {
        cache: 'no-store', signal: request.signal,
      });
      if (!response.ok) throw new Error('Refresh failed');
      const html = await response.text();
      if (request.signal.aborted) return;
      const updated = new DOMParser().parseFromString(html, 'text/html').getElementById('table-data');
      if (!updated) throw new Error('Missing table data');

      const position = { left: window.scrollX, top: window.scrollY };
      const scrolls = Array.from(content.querySelectorAll('.table-scroll'), element => ({
        name: element.getAttribute('aria-label'), left: element.scrollLeft,
      }));
      const focused = content.contains(document.activeElement) ? document.activeElement : null;
      content.replaceChildren(...Array.from(updated.childNodes, node => document.importNode(node, true)));
      for (const element of content.querySelectorAll('.table-scroll')) {
        element.scrollLeft = scrolls.find(item => item.name === element.getAttribute('aria-label'))?.left || 0;
      }
      if (focused) {
        const replacement = Array.from(content.querySelectorAll('button, a, [tabindex]')).find(element =>
          element.tagName === focused.tagName &&
          (focused.dataset.id ? element.dataset.id === focused.dataset.id :
            focused.hasAttribute('href') ? element.getAttribute('href') === focused.getAttribute('href') :
              element.getAttribute('aria-label') === focused.getAttribute('aria-label')));
        replacement?.focus({ preventScroll: true });
      }
      document.dispatchEvent(new Event('tables-refreshed'));
      window.scrollTo(position);
      lastRefresh = Date.now();
      updateAge();
    } catch {
      if (controller === request) {
        status.textContent = 'Unable to refresh. Existing data is unchanged.';
      }
    } finally {
      clearTimeout(timeout);
      if (controller === request) {
        controller = null;
        schedule();
      }
    }
  }

  select.addEventListener('change', () => {
    clearTimeout(timer);
    controller?.abort();
    controller = null;
    try { localStorage.setItem(storageKey, select.value); } catch { /* Optional preference. */ }
    if (select.value === '0') updateAge();
    else refresh();
  });
  schedule();
})();
