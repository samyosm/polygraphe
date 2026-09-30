import type { ReactNode } from "react";
import { cn } from "./cn";

export type TagColor = "gray" | "red" | "blue" | "green";

const colors: Record<TagColor, string> = {
  gray: "bg-tag-gray-bg text-tag-gray-ink",
  red: "bg-tag-red-bg text-tag-red-ink",
  blue: "bg-tag-blue-bg text-tag-blue-ink",
  green: "bg-tag-green-bg text-tag-green-ink",
};

export function Tag({
  color = "gray",
  pulse = false,
  children,
}: {
  color?: TagColor;
  pulse?: boolean;
  children: ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex h-6 items-center gap-1.5 rounded-full px-2 text-xs whitespace-nowrap",
        colors[color],
      )}
    >
      {pulse && (
        <span className="size-1.5 animate-pulse rounded-full bg-current" />
      )}
      {children}
    </span>
  );
}
