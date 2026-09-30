import type { ComponentProps, ReactNode } from "react";
import { cn } from "./cn";

// Carbon fields: grey fill, bottom border, focus outline.
const control =
  "w-full border-0 border-b border-line-strong bg-layer px-4 text-sm text-ink " +
  "placeholder:text-ink-placeholder outline-none focus:outline-2 focus:-outline-offset-2 focus:outline-focus";

interface FieldProps {
  label: string;
  hint?: string;
  children: ReactNode;
  className?: string;
}

export function Field({ label, hint, children, className }: FieldProps) {
  return (
    // biome-ignore lint/a11y/noLabelWithoutControl: the control is passed as children
    <label className={cn("flex flex-col gap-2", className)}>
      <span className="text-xs tracking-[0.32px] text-ink-muted">
        {label}
        {hint && <span className="text-ink-placeholder"> {hint}</span>}
      </span>
      {children}
    </label>
  );
}

export function TextInput({ className, ...props }: ComponentProps<"input">) {
  return <input className={cn(control, "h-10", className)} {...props} />;
}

export function TextArea({ className, ...props }: ComponentProps<"textarea">) {
  return (
    <textarea className={cn(control, "min-h-24 py-3", className)} {...props} />
  );
}

export function Select({ className, ...props }: ComponentProps<"select">) {
  return (
    <select
      className={cn(control, "h-10 cursor-pointer", className)}
      {...props}
    />
  );
}
