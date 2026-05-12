// Empty stub for browser. The Vendo SDK's main entry imports Node-only
// modules (crypto, fs, path, url) at the top of dist/index.js even though
// the browser doesn't use those code paths (Webhooks API, env-var loaders).
// An import map in index.html aliases the bare specifiers to this file so
// resolution succeeds. Accessing a member of this module will throw at
// runtime, which is fine because none of these are touched on the
// browser-Vendo code path.

// Common named exports the SDK pulls in — return throw-on-access proxies
// so the imports succeed but accidental use fails loudly.
// Stubs return harmless defaults instead of throwing — the SDK's chunk
// invokes some of these at MODULE LOAD time (e.g. fileURLToPath +
// dirname + join to compute PKG_DATA_DIR for the BYOK JSON). Throwing
// there crashes module evaluation before window.Vendo gets set.
// The actual runtime use cases (Webhooks.verify, BYOK env-var lookup)
// are never hit on the browser path.
export const createHmac = () => ({ update: () => ({ digest: () => "" }) });
export const timingSafeEqual = () => false;
export const readFileSync = () => "{}";
export const dirname = (p) => String(p || "").replace(/\/[^/]*$/, "") || ".";
export const join = (...parts) => parts.filter(Boolean).join("/");
export const fileURLToPath = (u) => {
  const s = typeof u === "string" ? u : (u && u.href) || "";
  return s.replace(/^file:\/\//, "") || "/";
};

export default {};
