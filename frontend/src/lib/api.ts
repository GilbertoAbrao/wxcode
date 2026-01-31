/**
 * API URL utilities.
 *
 * For HTTP requests: use the Next.js proxy (/api/...) so it works
 * regardless of where the frontend is accessed from.
 *
 * For WebSocket: connect directly to the backend since Next.js
 * doesn't proxy WebSocket. Derives host from window.location
 * so it works on any network.
 */

/** Backend port (must match uvicorn --port in start-dev.sh) */
const BACKEND_PORT = 8052;

/**
 * Get the backend WebSocket URL base.
 * Uses window.location.hostname + backend port so it works
 * both locally and over the network.
 */
export function getBackendWsUrl(): string {
  if (typeof window === "undefined") {
    // SSR fallback
    return `ws://localhost:${BACKEND_PORT}`;
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.hostname}:${BACKEND_PORT}`;
}

/**
 * Get the backend HTTP URL base (for direct calls that can't use the proxy,
 * e.g. large file uploads).
 */
export function getBackendHttpUrl(): string {
  if (typeof window === "undefined") {
    return `http://localhost:${BACKEND_PORT}`;
  }
  const protocol = window.location.protocol;
  return `${protocol}//${window.location.hostname}:${BACKEND_PORT}`;
}
