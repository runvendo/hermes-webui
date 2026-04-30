/**
 * Shared client-side state + polling for /api/connections.
 *
 * Both Providers tab and Integrations tab subscribe to this module.
 * Refreshes on:
 *   - Mount
 *   - visibilitychange → visible
 *   - 2s polling while any card is in `connecting` state (max 5 min)
 *   - 30s idle polling when tab is visible
 *
 * Exposed via window.VendoConnections so panels.js can consume without
 * needing ES module imports (hermes-webui static/ is plain script tags).
 */

(function () {
  const POLL_FAST_MS = 2000;
  const POLL_IDLE_MS = 30000;
  const CONNECTING_MAX_MS = 5 * 60 * 1000;

  const state = {
    connections: null,        // null = loading; [] = empty; [...] = populated
    lastFetchAt: 0,
    fetchError: null,
    connectingSince: new Map(),  // slug -> timestamp
  };

  const subscribers = new Set();

  function notify() {
    subscribers.forEach((cb) => {
      try { cb(state.connections, state.fetchError); }
      catch (e) { console.error("[vendo-connections] subscriber threw", e); }
    });
  }

  async function fetchConnections() {
    try {
      const res = await fetch("/api/connections", { credentials: "same-origin" });
      if (res.status === 503) {
        state.connections = [];
        state.fetchError = null;
      } else if (!res.ok) {
        state.fetchError = "HTTP " + res.status;
      } else {
        const body = await res.json();
        state.connections = body.connections;
        state.fetchError = null;
      }
    } catch (e) {
      state.fetchError = (e && e.message) || "fetch_failed";
    }
    state.lastFetchAt = Date.now();

    // Reconcile connecting-state timestamps.
    if (state.connections) {
      for (const c of state.connections) {
        if (c.status === "connected" && state.connectingSince.has(c.slug)) {
          state.connectingSince.delete(c.slug);
        }
      }
      for (const [slug, since] of state.connectingSince.entries()) {
        if (Date.now() - since > CONNECTING_MAX_MS) {
          state.connectingSince.delete(slug);
        }
      }
    }
    notify();
  }

  let pollTimer = null;
  function rescheduleLoop() {
    if (pollTimer) {
      clearTimeout(pollTimer);
      pollTimer = null;
    }
    if (document.hidden) return;
    const cadence = state.connectingSince.size > 0 ? POLL_FAST_MS : POLL_IDLE_MS;
    pollTimer = setTimeout(async () => {
      await fetchConnections();
      rescheduleLoop();
    }, cadence);
  }

  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) {
      fetchConnections().then(rescheduleLoop);
    } else if (pollTimer) {
      clearTimeout(pollTimer);
      pollTimer = null;
    }
  });

  window.addEventListener("focus", function () { fetchConnections(); });

  function subscribe(callback) {
    subscribers.add(callback);
    callback(state.connections, state.fetchError);
    return function unsubscribe() { subscribers.delete(callback); };
  }

  function refresh() { return fetchConnections(); }

  function startConnecting(slug) {
    state.connectingSince.set(slug, Date.now());
    rescheduleLoop();
    notify();
  }

  function isConnecting(slug) {
    return state.connectingSince.has(slug);
  }

  function openSetupTab(setupUrl, slug) {
    startConnecting(slug);
    window.open(setupUrl, "_blank", "noopener");
  }

  // Initial load + reschedule.
  fetchConnections().then(rescheduleLoop);

  // Public API.
  window.VendoConnections = {
    subscribe: subscribe,
    refresh: refresh,
    startConnecting: startConnecting,
    isConnecting: isConnecting,
    openSetupTab: openSetupTab,
  };
})();
