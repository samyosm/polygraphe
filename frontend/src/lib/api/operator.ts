import "server-only";

import { cookies } from "next/headers";
import createClient from "openapi-fetch";
import { cache } from "react";
import { API_URL } from "@/lib/config";
import { api } from "./client";
import type { paths } from "./schema";

/** httpOnly cookie holding the operator session token issued by the server. */
export const OPERATOR_COOKIE = "polygraphe_operator";

async function operatorToken(): Promise<string | undefined> {
  return (await cookies()).get(OPERATOR_COOKIE)?.value;
}

/** Whether this visitor may control trials. Checked with the server once per request. */
export const isOperator = cache(async (): Promise<boolean> => {
  const token = await operatorToken();
  if (!token) return false;
  const { response } = await api.GET("/auth/operator", {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.ok;
});

/** Client authenticated as the operator, for mutations. */
export async function operatorApi() {
  const token = await operatorToken();
  return createClient<paths>({
    baseUrl: API_URL,
    cache: "no-store",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
}
