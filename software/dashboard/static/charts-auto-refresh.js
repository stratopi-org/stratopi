(() => {
  const select = document.getElementById('charts-auto-refresh');
  const status = document.getElementById('charts-refresh-status');
  const storageKey = 'stratopi.chartsAutoRefreshSeconds';
  const allowed = ['0', '15', '30', '60', '120'];
  let timer;
  let ageTimer;
  let lastRefresh = null;

  try {
    const saved = localStorage.getItem(storageKey);
    if (allowed.includes(saved)) select.value = saved;
  } catch { /* Browser storage is optional. */ }

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

  function requestRefresh() {
    clearTimeout(timer);
    clearTimeout(ageTimer);
    status.textContent = 'Refreshing…';
    document.dispatchEvent(new CustomEvent('charts:refresh-request'));
  }

  document.addEventListener('charts:loading', () => {
    clearTimeout(timer);
    clearTimeout(ageTimer);
    status.textContent = select.value === '0' ? '' : 'Refreshing…';
  });
  document.addEventListener('charts:refreshed', event => {
    clearTimeout(timer);
    clearTimeout(ageTimer);
    if (select.value === '0') {
      status.textContent = '';
      return;
    }
    if (event.detail.success) {
      lastRefresh = Date.now();
      updateAge();
    } else {
      status.textContent = 'Unable to refresh. Retrying at the next interval.';
    }
    // Start the interval after the entire chart batch has completed.
    timer = setTimeout(requestRefresh, Number(select.value) * 1000);
  });
  select.addEventListener('change', () => {
    clearTimeout(timer);
    clearTimeout(ageTimer);
    try { localStorage.setItem(storageKey, select.value); } catch { /* Optional preference. */ }
    if (select.value === '0') status.textContent = '';
    else requestRefresh();
  });
})();
