"use client";

import { Close, Locked, Unlocked } from "@carbon/icons-react";
import { useTranslations } from "next-intl";
import { useActionState, useId } from "react";
import { Button } from "@/components/ui/button";
import { Field, TextInput } from "@/components/ui/field";
import { signIn, signOut } from "./actions";

const headerButton =
  "flex h-10 items-center gap-2 px-2 text-sm text-ink-muted hover:bg-layer-hover hover:text-ink " +
  "outline-none focus-visible:outline-2 focus-visible:outline-focus";

/**
 * Operator mode: unlocked with the operator password, it shows the controls (create,
 * edit, start, stop, save). Everyone else can only watch.
 */
export function OperatorMenu({ signedIn }: { signedIn: boolean }) {
  const t = useTranslations("operator");

  if (signedIn) {
    return (
      <form action={signOut}>
        <button type="submit" className={headerButton} title={t("lockHint")}>
          <Unlocked size={20} aria-hidden />
          <span className="hidden sm:inline">{t("lock")}</span>
        </button>
      </form>
    );
  }

  return <SignInPopover />;
}

function SignInPopover() {
  const t = useTranslations("operator");
  const [state, action, pending] = useActionState(signIn, undefined);
  const popoverId = useId();

  return (
    <>
      <button type="button" popoverTarget={popoverId} className={headerButton}>
        <Locked size={20} aria-hidden />
        <span className="hidden sm:inline">{t("operator")}</span>
      </button>
      {/* Native popover: light dismiss, Escape and focus handling for free. */}
      <div
        id={popoverId}
        popover="auto"
        className="m-auto w-[min(24rem,calc(100vw-2rem))] bg-background p-0 text-ink shadow-xl backdrop:bg-shell/50"
      >
        <form action={action} className="flex flex-col gap-6 p-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex flex-col gap-1">
              <h2 className="text-xl font-light">{t("title")}</h2>
              <p className="text-ink-muted">{t("hint")}</p>
            </div>
            <button
              type="button"
              popoverTarget={popoverId}
              popoverTargetAction="hide"
              aria-label={t("close")}
              className="p-1 text-ink-muted hover:bg-layer-hover"
            >
              <Close size={20} aria-hidden />
            </button>
          </div>
          <Field label={t("password")}>
            <TextInput
              name="password"
              type="password"
              required
              autoComplete="current-password"
            />
          </Field>
          {state?.error && (
            <p role="alert" className="text-support-error">
              {state.error}
            </p>
          )}
          <Button
            type="submit"
            icon={Unlocked}
            disabled={pending}
            className="w-full"
          >
            {t("unlock")}
          </Button>
        </form>
      </div>
    </>
  );
}
