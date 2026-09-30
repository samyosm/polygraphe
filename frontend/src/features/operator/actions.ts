"use server";

import { refresh } from "next/cache";
import { cookies } from "next/headers";
import { getTranslations } from "next-intl/server";
import { api } from "@/lib/api/client";
import { OPERATOR_COOKIE } from "@/lib/api/operator";

export type SignInResult = { error: string } | undefined;

export async function signIn(
  _: SignInResult,
  form: FormData,
): Promise<SignInResult> {
  const password = form.get("password");
  const { data } = await api.POST("/auth/operator", {
    body: { password: typeof password === "string" ? password : "" },
  });
  if (!data)
    return { error: (await getTranslations("errors"))("wrongPassword") };

  (await cookies()).set(OPERATOR_COOKIE, data.token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    expires: new Date(data.expires_at),
  });
  refresh();
}

export async function signOut() {
  (await cookies()).delete(OPERATOR_COOKIE);
  refresh();
}
