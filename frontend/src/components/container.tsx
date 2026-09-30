import type { ReactNode } from "react";
import { cn } from "./ui/cn";

/** Horizontal page frame shared by the header, the hero and every page. */
export function Container({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <div className={cn("mx-auto w-full max-w-7xl px-4 md:px-8", className)}>
      {children}
    </div>
  );
}
