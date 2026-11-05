const tooltip = document.getElementById('id-popover');
const notification = document.getElementById('clipboard-notification');
let activeTrigger = null;
let hideTimer;
let notificationTimer;

function notify(message) {
  clearTimeout(notificationTimer);
  notification.textContent = message;
  notificationTimer = setTimeout(() => { notification.textContent = ''; }, 3000);
}

async function copyId(trigger) {
  try {
    await navigator.clipboard.writeText(trigger.dataset.id);
    notify('id copied to clipboard.');
  } catch {
    notify('Unable to copy the id. Select and copy it from the popover.');
  }
}

function hideId() {
  clearTimeout(hideTimer);
  tooltip.hidden = true;
  activeTrigger = null;
}

function showId(trigger) {
  clearTimeout(hideTimer);
  activeTrigger = trigger;
  tooltip.textContent = trigger.dataset.id;
  tooltip.hidden = false;
  const anchor = trigger.getBoundingClientRect();
  const box = tooltip.getBoundingClientRect();
  const left = Math.max(12, Math.min(anchor.left, window.innerWidth - box.width - 12));
  const below = anchor.bottom + 8;
  const top = below + box.height <= window.innerHeight - 12
    ? below : Math.max(12, anchor.top - box.height - 8);
  tooltip.style.left = `${left}px`;
  tooltip.style.top = `${top}px`;
}

function scheduleHide() {
  clearTimeout(hideTimer);
  hideTimer = setTimeout(() => {
    if (activeTrigger && document.activeElement === activeTrigger) return;
    hideId();
  }, 150);
}

// Delegate events so large tables need only one set of listeners.
document.addEventListener('pointerover', (event) => {
  const trigger = event.target.closest('.id-trigger');
  if (trigger) showId(trigger);
  if (tooltip.contains(event.target)) clearTimeout(hideTimer);
});
document.addEventListener('pointerout', (event) => {
  if (event.target.closest('.id-trigger') || tooltip.contains(event.target)) scheduleHide();
});
document.addEventListener('focusin', (event) => {
  if (event.target.matches('.id-trigger')) showId(event.target);
});
document.addEventListener('focusout', (event) => {
  if (event.target.matches('.id-trigger')) scheduleHide();
});
document.addEventListener('click', (event) => {
  const trigger = event.target.closest('.id-trigger');
  if (trigger) {
    showId(trigger);
    copyId(trigger);
  }
  else if (!tooltip.contains(event.target)) hideId();
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') hideId();
});
document.addEventListener('scroll', hideId, true);
window.addEventListener('resize', hideId);
document.addEventListener('tables-refreshed', hideId);
