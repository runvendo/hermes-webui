// Sidebar identity chip. Identity from server-injected <meta> tags;
// balance from the SDK client (window.Vendo.billing.balance()).

const PALETTE = [
  '#2563eb', '#9333ea', '#db2777', '#dc2626',
  '#ea580c', '#16a34a', '#0891b2', '#475569',
];

// The Vendo dashboard always lives at vendo.run, regardless of the API base.
// (vendo-base-url meta is the *API* base — in dev it's "/api/vendo/proxy".)
const BILLING_URL = 'https://vendo.run/billing';

function pickColor(userId) {
  if (!userId) return '#6b7280'; // neutral gray when we have no stable id
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

function formatBalance(micros) {
  if (typeof micros !== 'number' || !isFinite(micros)) return '';
  return `$${(micros / 1_000_000).toFixed(2)} credits`;
}

async function renderVendoChip() {
  const root = document.getElementById('vendo-identity-chip');
  if (!root) return;
  const ident = window.VendoIdentity || {};

  // Render if we have ANY identifying info — userId is preferred but not required.
  if (!ident.userId && !ident.email && !ident.name) {
    root.hidden = true;
    console.info('[vendo-chip] hidden: no identity in <meta> tags');
    return;
  }

  const name = ident.name || ident.email || 'User';
  const avatar = root.querySelector('.vendo-identity-chip__avatar');
  const nameEl = root.querySelector('.vendo-identity-chip__name');
  const linkEl = root.querySelector('.vendo-identity-chip__credits-link');
  const creditsEl = root.querySelector('.vendo-identity-chip__credits');

  if (avatar) {
    avatar.style.backgroundColor = pickColor(ident.userId);
    avatar.textContent = initials(name);
  }
  if (nameEl) nameEl.textContent = name;
  if (linkEl) linkEl.setAttribute('href', BILLING_URL);

  root.removeAttribute('hidden');

  if (creditsEl && linkEl && window.Vendo) {
    try {
      const b = await window.Vendo.billing.balance();
      const text = formatBalance(b.creditsRemainingMicros);
      if (text) {
        creditsEl.textContent = text;
        linkEl.removeAttribute('hidden');
      }
    } catch (err) {
      console.info('[vendo-chip] balance fetch failed:', err);
    }
  } else if (!window.Vendo) {
    console.info('[vendo-chip] balance not loaded: window.Vendo not initialized');
  }
}

document.addEventListener('vendo:ready', renderVendoChip);
document.addEventListener('vendo:connection-changed', () => {
  const creditsEl = document.querySelector('.vendo-identity-chip__credits');
  const linkEl = document.querySelector('.vendo-identity-chip__credits-link');
  if (!creditsEl || !linkEl || !window.Vendo) return;
  window.Vendo.billing.balance().then(b => {
    const text = formatBalance(b.creditsRemainingMicros);
    if (text) {
      creditsEl.textContent = text;
      linkEl.removeAttribute('hidden');
    }
  }).catch(err => {
    console.info('[vendo-chip] balance refresh failed:', err);
  });
});
