// Sidebar identity chip. Identity from server-injected <meta> tags;
// balance from the SDK client (window.Vendo.billing.balance()).

const PALETTE = [
  '#2563eb', '#9333ea', '#db2777', '#dc2626',
  '#ea580c', '#16a34a', '#0891b2', '#475569',
];

function pickColor(userId) {
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
  if (!ident.userId) { root.hidden = true; return; }

  const name = ident.name || ident.email || 'User';
  const avatar = root.querySelector('.vendo-identity-chip__avatar');
  const nameEl = root.querySelector('.vendo-identity-chip__name');
  const creditsEl = root.querySelector('.vendo-identity-chip__credits');

  if (avatar) { avatar.style.backgroundColor = pickColor(ident.userId); avatar.textContent = initials(name); }
  if (nameEl) nameEl.textContent = name;

  root.removeAttribute('hidden');

  if (creditsEl && window.Vendo) {
    try {
      const b = await window.Vendo.billing.balance();
      const text = formatBalance(b.creditsRemainingMicros);
      if (text) { creditsEl.textContent = text; creditsEl.hidden = false; }
    } catch (_) {}
  }
}

document.addEventListener('vendo:ready', renderVendoChip);
document.addEventListener('vendo:connection-changed', () => {
  const creditsEl = document.querySelector('.vendo-identity-chip__credits');
  if (!creditsEl || !window.Vendo) return;
  window.Vendo.billing.balance().then(b => {
    const text = formatBalance(b.creditsRemainingMicros);
    if (text) creditsEl.textContent = text;
  }).catch(() => {});
});
