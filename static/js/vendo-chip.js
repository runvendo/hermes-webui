// static/js/vendo-chip.js
// Renders a small chip in the sidebar bottom showing the signed-in Vendo
// user. Hidden when not behind Vendo SSO. Spec:
// docs/superpowers/specs/2026-04-28-hermes-vendo-sso-design.md

const PALETTE = [
  '#2563eb', // blue
  '#9333ea', // purple
  '#db2777', // pink
  '#dc2626', // red
  '#ea580c', // orange
  '#16a34a', // green
  '#0891b2', // cyan
  '#475569', // slate
];

function pickColor(userId) {
  // Take the first 8 hex chars of the user_id (or its hash if non-hex)
  // and mod by palette length. Deterministic per user.
  const hex = (userId || '').replace(/[^0-9a-f]/gi, '').slice(0, 8);
  const n = parseInt(hex || '0', 16);
  return PALETTE[(isNaN(n) ? 0 : n) % PALETTE.length];
}

function initials(name) {
  const parts = (name || '').trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0][0].toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

// Shared balance fetch — single request per page load, reused by the chip and
// the Vendo panel identity card. Returns a Promise that resolves to a number
// (USD) or null when unavailable.
window.VendoBalance = window.VendoBalance || {
  _promise: null,
  get() {
    if (this._promise) return this._promise;
    this._promise = fetch('/api/vendo/balance', { credentials: 'same-origin' })
      .then(r => r.ok ? r.json() : null)
      .then(b => (b && typeof b.balance_usd === 'number') ? b.balance_usd : null)
      .catch(() => null);
    return this._promise;
  },
};

async function loadVendoChip() {
  let res;
  try {
    res = await fetch('/api/vendo/identity', {
      credentials: 'same-origin',
      headers: { 'Accept': 'application/json' },
    });
  } catch (_e) {
    return;  // network error — leave chip hidden
  }
  if (!res.ok) return;  // 404 means SSO off; nothing to show
  const id = await res.json();
  if (!id || !id.user_id) return;

  const root = document.getElementById('vendo-identity-chip');
  if (!root) return;
  const avatar = root.querySelector('.vendo-identity-chip__avatar');
  const nameEl = root.querySelector('.vendo-identity-chip__name');
  const creditsEl = root.querySelector('.vendo-identity-chip__credits');

  avatar.style.backgroundColor = pickColor(id.user_id);
  avatar.textContent = initials(id.name);
  nameEl.textContent = id.name;

  // Populate credits line lazily — same source as the Vendo panel identity card.
  if (creditsEl) {
    window.VendoBalance.get().then(usd => {
      if (usd === null) return;
      creditsEl.textContent = `$${usd.toFixed(2)} credits`;
      creditsEl.hidden = false;
    });
  }

  root.addEventListener('click', () => {
    window.open(id.dashboard_url, '_blank', 'noopener');
  });

  // Right-click / long-press for "Sign out of Vendo".
  root.addEventListener('contextmenu', (ev) => {
    ev.preventDefault();
    if (confirm('Sign out of Vendo? This signs you out of every Vendo deployment.')) {
      window.location.href = id.logout_url;
    }
  });

  root.removeAttribute('hidden');
}

// Run after DOM ready.
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', loadVendoChip);
} else {
  loadVendoChip();
}
