import "server-only";

import { notFound } from "next/navigation";
import createClient from "openapi-fetch";
import { API_URL } from "@/lib/config";
import type { paths } from "./schema";

/** Typed client for the processing server. Server-side only: pages and server actions. */
export const api = createClient<paths>({ baseUrl: API_URL, cache: "no-store" });

/** Data of a successful response; 404 renders the not-found page, other errors throw. */
export function unwrap<T>(result: { data?: T; response: Response }): T {
  if (result.response.status === 404) notFound();
  if (result.data === undefined) {
    throw new Error(`${result.response.status} ${result.response.statusText}`);
  }
  return result.data;
}
