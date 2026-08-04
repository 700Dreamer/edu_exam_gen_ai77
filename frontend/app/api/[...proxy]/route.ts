/**
 * Streaming proxy for all /api/* requests to the FastAPI backend.
 * Replaces the next.config.ts rewrites() for the /api path.
 *
 * WHY THIS EXISTS:
 * Next.js rewrites() and its built-in proxy buffer request bodies in memory
 * before forwarding them. The default buffer cap is ~4MB, which causes
 * multipart uploads of 4+ scanner pages (~800KB JPEG each) to fail with a 500.
 * A Route Handler with `export const config` disabling body parsing streams
 * the request body directly with no size limit.
 */

import { NextRequest } from "next/server";

const BACKEND_URL = "http://127.0.0.1:8000";

// Disable Next.js body parsing -- let us stream the raw request body
export const dynamic = "force-dynamic";
export const maxDuration = 300; // 5-minute max for large batch uploads

async function handler(req: NextRequest) {
  const { pathname, search } = req.nextUrl;
  const backendUrl = `${BACKEND_URL}${pathname}${search}`;

  // Build forwarded headers (strip host, set correct content-type, keep auth)
  const headers = new Headers();
  req.headers.forEach((value, key) => {
    const lower = key.toLowerCase();
    // Skip headers that should not be forwarded
    if (["host", "connection", "transfer-encoding"].includes(lower)) return;
    headers.set(key, value);
  });

  const response = await fetch(backendUrl, {
    method: req.method,
    headers,
    // Stream the body directly -- no buffering, no size limit
    body: req.method !== "GET" && req.method !== "HEAD" ? req.body : undefined,
    // @ts-ignore -- Node.js fetch supports duplex for streaming bodies
    duplex: "half",
  });

  // Stream the response back to the client
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
}

export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const PATCH = handler;
export const DELETE = handler;
export const OPTIONS = handler;
