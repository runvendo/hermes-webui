import { Vendo } from "/static/vendor/vendodev-sdk/index.js";
import "/static/vendor/vendodev-sdk/browser/index.js";

function readMeta(name) {
  const el = document.querySelector(`meta[name="${name}"]`);
  return el ? el.getAttribute("content") || "" : "";
}

const apiKey = readMeta("vendo-api-key");
if (apiKey) {
  const baseUrl = readMeta("vendo-base-url") || "https://vendo.run";
  // Bind fetch to globalThis: the SDK stores the function reference and later
  // calls `this.fetch(...)` from instance scope, so an unbound builtin throws
  // "Failed to execute 'fetch' on 'Window': Illegal invocation". Pre-binding
  // here works around @vendodev/sdk@0.2.0 not binding internally.
  window.Vendo = new Vendo({
    apiKey,
    baseUrl,
    fetch: globalThis.fetch.bind(globalThis),
  });
  window.VendoIdentity = {
    userId: readMeta("vendo-user-id") || null,
    email: readMeta("vendo-user-email") || null,
    name: readMeta("vendo-user-name") || null,
  };
  document.documentElement.classList.add("vendo-active");
  document.dispatchEvent(new CustomEvent("vendo:ready"));
} else {
  document.documentElement.classList.add("vendo-inactive");
}
