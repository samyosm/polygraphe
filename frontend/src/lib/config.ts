/**
 * Processing server as the browser reaches it (live websockets), e.g.
 * "https://polygraphe.samy.dev/api". Inlined at build time, like every NEXT_PUBLIC_ variable.
 */
export const PUBLIC_API_URL = trimSlash(
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
);

/**
 * Processing server as the Next.js server reaches it, e.g. "http://backend:8000" inside
 * Docker. Read at runtime; defaults to the public URL.
 */
export const API_URL = trimSlash(process.env.API_URL ?? PUBLIC_API_URL);

export const WS_URL = PUBLIC_API_URL.replace(/^http/, "ws");

function trimSlash(url: string): string {
  return url.replace(/\/+$/, "");
}
