import type { CarbonIconType } from "@carbon/icons-react";
import Link from "next/link";
import type { ComponentProps, ReactNode } from "react";
import { cn } from "./cn";

type Variant = "primary" | "secondary" | "tertiary" | "ghost" | "danger";

// Carbon buttons: square, label on the left, icon pushed to the right...
const wide = "min-w-40 justify-between gap-8";

const variants: Record<Variant, string> = {
  primary: `${wide} bg-interactive text-ink-on-color hover:bg-interactive-hover active:bg-interactive-active`,
  secondary: `${wide} bg-secondary text-ink-on-color hover:bg-secondary-hover`,
  tertiary: `${wide} border border-interactive text-interactive hover:bg-interactive hover:text-ink-on-color`,
  // ...except ghost buttons, which take their natural width.
  ghost: "gap-4 text-interactive hover:bg-layer-hover",
  danger: `${wide} bg-danger text-ink-on-color hover:opacity-90`,
};

const base =
  "inline-flex h-12 items-center px-4 text-sm transition-colors " +
  "outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus " +
  "disabled:cursor-not-allowed disabled:border-transparent disabled:bg-disabled disabled:text-ink-disabled";

interface OwnProps {
  variant?: Variant;
  icon?: CarbonIconType;
  children: ReactNode;
}

function Content({
  icon: Icon,
  children,
}: Pick<OwnProps, "icon" | "children">) {
  return (
    <>
      <span>{children}</span>
      {Icon && <Icon size={16} aria-hidden />}
    </>
  );
}

export function Button({
  variant = "primary",
  icon,
  children,
  className,
  type = "button",
  ...props
}: OwnProps & ComponentProps<"button">) {
  return (
    <button
      type={type}
      className={cn(base, variants[variant], className)}
      {...props}
    >
      <Content icon={icon}>{children}</Content>
    </button>
  );
}

export function ButtonLink({
  variant = "primary",
  icon,
  children,
  className,
  ...props
}: OwnProps & ComponentProps<typeof Link>) {
  return (
    <Link className={cn(base, variants[variant], className)} {...props}>
      <Content icon={icon}>{children}</Content>
    </Link>
  );
}
