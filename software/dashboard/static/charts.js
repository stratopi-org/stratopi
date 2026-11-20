(() => {
  let activeRequest;
  const charts = Array.from(document.querySelectorAll('[data-chart-url]'), panel => ({
    panel,
    plot: panel.querySelector('.chart-plot'),
    status: panel.querySelector('.chart-status'),
    renderQueue: Promise.resolve(),
  }));

  async function updateChart(chart, range, request) {
    const { panel, plot, status } = chart;
    panel.setAttribute('aria-busy', 'true');
    status.textContent = 'Loading chart…';
    try {
      if (typeof Plotly === 'undefined') throw new Error('Plotly is unavailable. Reload the page to try again.');
      const url = new URL(panel.dataset.chartUrl, window.location.origin);
      url.searchParams.set('start', range.start);
      url.searchParams.set('end', range.end);
      const response = await fetch(url, { signal: request.signal, cache: 'no-store' });
      const figure = await response.json();
      if (request.signal.aborted) return false;
      if (!response.ok) throw new Error(figure.error || 'Unable to load chart data.');

      // Plotly Date objects use browser-local time, matching the time picker.
      for (const trace of figure.data) trace.x = trace.x.map(value => new Date(value));
      figure.layout.xaxis.range = figure.layout.xaxis.range.map(value => new Date(value));
      for (const annotation of figure.layout.annotations || []) {
        if (annotation.xref === 'x') annotation.x = new Date(annotation.x);
      }
      figure.layout.xaxis.title.text = 'added';
      chart.renderQueue = chart.renderQueue.catch(() => {}).then(async () => {
        if (request.signal.aborted) return;
        plot.hidden = false;
        await Plotly.react(plot, figure.data, figure.layout, { responsive: true, displaylogo: false });
      });
      await chart.renderQueue;
      if (request.signal.aborted) return false;
      status.textContent = figure.layout.meta.row_count === 0 ? 'No data in this time range.' : '';
      return true;
    } catch (error) {
      if (activeRequest !== request) return false;
      plot.hidden = true;
      status.textContent = request.signal.aborted
        ? 'Chart request timed out. Try again or choose a smaller time range.'
        : error.message || 'Unable to load chart data. Try another time range.';
      return false;
    } finally {
      if (activeRequest === request) panel.setAttribute('aria-busy', 'false');
    }
  }

  // One batch per shared range, with a completion event for the refresh scheduler.
  document.addEventListener('charts:range-change', async event => {
    activeRequest?.abort();
    const request = new AbortController();
    activeRequest = request;
    const timeout = setTimeout(() => request.abort(), 45000);
    document.dispatchEvent(new CustomEvent('charts:loading'));
    try {
      const updates = charts.map(chart => updateChart(chart, event.detail, request));
      if (window.DashboardLocationMap) updates.push(window.DashboardLocationMap.update(event.detail, request.signal));
      const results = await Promise.all(updates);
      if (activeRequest === request) {
        document.dispatchEvent(new CustomEvent('charts:refreshed', {
          detail: { success: results.every(Boolean) },
        }));
      }
    } finally {
      clearTimeout(timeout);
    }
  });
})();
