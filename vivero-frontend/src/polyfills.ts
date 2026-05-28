declare global {
  interface Window {
    global?: typeof globalThis;
  }

  // Vite/browser bundles do not expose `global` by default, but some legacy
  // dependencies still expect it at module-evaluation time.
  // eslint-disable-next-line no-var
  var global: typeof globalThis;
}

if (typeof window !== "undefined") {
  if (typeof window.global === "undefined") {
    window.global = window;
  }
}

if (typeof globalThis !== "undefined" && typeof globalThis.global === "undefined") {
  globalThis.global = globalThis;
}

export {};
